import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
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
        self.rag_chain = None
        self.vectorstore = None

        if self.groq_api_key:
            self.llm = ChatGroq(model_name="openai/gpt-oss-120b", groq_api_key=self.groq_api_key)
        else:
            self.llm = None

    def process_pdf(self, file_path: str):
        """Charge, découpe et indexe le document PDF dans FAISS."""
        loader = PyPDFLoader(file_path)
        docs = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)

        self.vectorstore = FAISS.from_documents(splits, self.embeddings)
        retriever = self.vectorstore.as_retriever()

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

    def ask(self, question: str) -> str:
        """Exécute la chaîne RAG pour répondre à la question."""
        if not self.rag_chain:
            raise ValueError("Aucun document n'a été indexé. Veuillez d'abord charger un PDF.")
        
        response = self.rag_chain.invoke({"input": question})
        return response["answer"]