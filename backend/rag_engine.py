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
        
        # --- MODIFICATION 1 : S'adapter à la CI/CD ---
        # On lit la variable OPENAI_API_KEY (qui contient votre clé Groq injectée par GitHub)
        self.groq_api_key = os.getenv("OPENAI_API_KEY") 
        
        self.persist_directory = "./chroma_db"
        self.vectorstore = None
        self.rag_chain = None

        if self.groq_api_key:
            self.llm = ChatGroq(model_name="openai/gpt-oss-120b", groq_api_key=self.groq_api_key)
        else:
            print("⚠️ ATTENTION : Aucune clé API trouvée dans l'environnement.")
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
            
            if not self.vectorstore:
                print("-> _setup_chain annulé : vectorstore manquant.")
                return
            if not self.llm:
                print("-> _setup_chain annulé : LLM manquant (clé API non chargée).")
                return
            
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
            
            # --- NOUVEAU PROMPT STORYTELLING ---
            system_prompt = (
                "Tu es SN-Career-AI, un coach de carrière expert et un analyseur ATS impitoyable mais ultra-constructif. "
                "Ton objectif est d'aider le candidat à décrocher des entretiens en optimisant son profil. "
                "Utilise le contexte fourni (le CV du candidat) pour répondre à la requête de l'utilisateur (qui est souvent une offre d'emploi ou une question de préparation). "
                "Sois direct, professionnel, et structure toujours tes réponses avec : "
                "1. Un score ou avis de compatibilité clair. "
                "2. Les points forts du CV pour ce poste. "
                "3. Les lacunes à combler ou les mots-clés manquants. "
                "Si la question sort du cadre de la recherche d'emploi, ramène la conversation sur l'optimisation de carrière.\n\n"
                "Contexte du CV :\n{context}"
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