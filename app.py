import os
import streamlit as st
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
# Utilisation d'un modèle d'embedding léger et performant via HuggingFace (ou alternatif) 
# Note: Pour faire simple sans clé OpenAI, on utilise un modèle open-source léger pour les embeddings ou une alternative textuelle.
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# Charger les variables d'environnement
load_dotenv()

st.set_page_config(page_title="Assistant RAG d'Entreprise", page_icon="🤖")

st.title("📄 Assistant Documentaire Intelligent (RAG)")
st.markdown("Interrogez vos documents techniques en toute sécurité.")

# Vérification de la clé API
groq_api_key = os.getenv("GROQ_API_KEY")

uploaded_file = st.file_uploader("Téléchargez un document PDF", type=["pdf"])

if uploaded_file is not None:
    # Sauvegarde temporaire du PDF uploadé pour que PyPDFLoader puisse le lire
    os.makedirs("data", exist_ok=True)
    file_path = os.path.join("data", uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.success(f"Fichier '{uploaded_file.name}' bien reçu et stocké !")

    with st.spinner("Indexation et découpage du document en cours..."):
        # 1. Charger le PDF
        loader = PyPDFLoader(file_path)
        docs = loader.load()

        # 2. Découper le texte en chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)

        # 3. Créer les embeddings et la base vectorielle FAISS
        # On utilise un modèle d'embedding gratuit et léger qui tourne en local sur le CPU
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vectorstore = FAISS.from_documents(splits, embeddings)
        retriever = vectorstore.as_retriever()

    st.success("Document indexé avec succès dans la base vectorielle !")

    # 4. Configurer le modèle LLM Groq
    if not groq_api_key:
        st.error("Veuillez renseigner votre GROQ_API_KEY dans le fichier .env")
    else:
        llm = ChatGroq(model_name="openai/gpt-oss-120b", groq_api_key=groq_api_key)

        # 5. Créer la chaîne RAG
        system_prompt = (
            "Vous êtes un assistant technique expert. "
            "Utilisez les contextes suivants pour répondre à la question posée. "
            "Si vous ne connaissez pas la réponse, dites clairement que vous ne savez pas.\n\n"
            "{context}"
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])

        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        rag_chain = create_retrieval_chain(retriever, question_answer_chain)

        # 6. Interface de chat / question
        user_query = st.text_input("Posez une question sur votre document :")

        if user_query:
            with st.spinner("Recherche de la réponse..."):
                response = rag_chain.invoke({"input": user_query})
                st.subheader("Réponse :")
                st.write(response["answer"])

else:
    st.info("Veuillez importer un fichier PDF pour commencer.")