import requests
import os

API_URL = os.getenv("BACKEND_URL", "http://backend:8000")

def check_health():
    try:
        return requests.get(f"{API_URL}/health", timeout=3).status_code == 200
    except:
        return False

def upload_pdf(file_name, file_bytes):
    files = {"file": (file_name, file_bytes, "application/pdf")}
    return requests.post(f"{API_URL}/upload", files=files)

def ask_question(question: str, history: list):
    payload = {
        "question": question,
        "history": history
    }
    return requests.post(f"{API_URL}/chat", json=payload)