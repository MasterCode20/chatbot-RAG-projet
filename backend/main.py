import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from backend.rag_engine import RAGEngine

app = FastAPI(
    title="RAG Enterprise API",
    description="API REST pour l'ingestion et le query RAG",
    version="0.2.0"
)

# Instance globale du moteur RAG
rag_service = RAGEngine()

UPLOAD_DIR = "data"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class QuestionRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    answer: str


@app.get("/health")
def health_check():
    return {"status": "ok", "groq_configured": bool(rag_service.groq_api_key)}


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont acceptés.")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        rag_service.process_pdf(file_path)
        return {"filename": file.filename, "status": "indexé avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'indexation : {str(e)}")


@app.post("/chat", response_model=AnswerResponse)
async def chat(request: QuestionRequest):
    try:
        answer = rag_service.ask(request.question)
        return AnswerResponse(answer=answer)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur : {str(e)}")