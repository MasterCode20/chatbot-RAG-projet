import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

class RAGEngine:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.persist_directory = "./chroma_db"
        self.vectorstore = None
        self.rag_chain = None

        if self.groq_api_key:
            self.llm = ChatGroq(model_name="openai/gpt-oss-120b", groq_api_key=self.groq_api_key)
        else:
            self.llm = None

        # Charger la base vectorielle existante sur disque si elle y est déjà
        self._init_vectorstore()

    def _init_vectorstore(self):
        """Initialise ou recharge la base Chroma depuis le disque."""
        if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
            try:
                self.vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
                self._setup_chain()
                print("-> Base vectorielle Chroma chargée depuis le disque avec succès.")
            except Exception as e:
                print(f"-> Erreur lors du chargement de la base persistante : {e}")

    def _setup_chain(self):
        """Configure la chaîne RAG avec le retriever actuel."""
        if not self.vectorstore or not self.llm:
            return
        
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
        
        system_prompt = (
            "Vous êtes un assistant technique expert.\n"
            "Utilisez les contextes suivants pour répondre à la question posée.\n"
            "Si vous ne connaissez pas la réponse, dites clairement que vous ne savez pas.\n\n"
            "{context}"
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])

        question_answer_chain = create_stuff_documents_chain(self.llm, prompt)
        self.rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    def process_pdf(self, file_path: str):
        """Charge, découpe et indexe un nouveau PDF dans Chroma (avec persistance)."""
        loader = PyPDFLoader(file_path)
        docs = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)

        # Créer et persister la base Chroma
        self.vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        
        # Mettre à jour la chaîne RAG
        self._setup_chain()

    def ask(self, question: str) -> str:
        """Exécute la chaîne RAG pour répondre à la question."""
        if not self.rag_chain:
            raise ValueError("Aucun document n'a été indexé ou chargé. Veuillez d'abord charger un PDF.")
        
        response = self.rag_chain.invoke({"input": question})
        return response["answer"]