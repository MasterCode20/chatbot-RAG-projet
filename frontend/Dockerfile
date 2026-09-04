FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

# AJOUT : Forcer PyTorch en version CPU pour le frontend
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]