import requests
import os

API_URL = os.getenv("BACKEND_URL", "http://backend:8000")

def check_health():
    """Vérifie si le backend FastAPI est accessible."""
    try:
        return requests.get(f"{API_URL}/health", timeout=3).status_code == 200
    except:
        return False

def upload_pdf(file_name, file_bytes):
    """Envoie le CV au backend pour vectorisation dans ChromaDB."""
    files = {"file": (file_name, file_bytes, "application/pdf")}
    return requests.post(f"{API_URL}/upload", files=files)

def ask_question(question: str, history: list):
    """Envoie la question et l'historique conversationnel au backend."""
    payload = {
        "question": question,
        "history": history
    }
    return requests.post(f"{API_URL}/chat", json=payload)