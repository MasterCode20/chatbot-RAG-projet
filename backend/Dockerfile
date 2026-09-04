FROM python:3.12-slim

WORKDIR /app

# 1. Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 2. Copier le fichier des dépendances
COPY requirements.txt .

# 3. Installer PyTorch en version CPU uniquement (gain de place massif)
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 4. Installer le reste des dépendances du projet
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copier le code source
COPY . .

# 6. Exposer le port FastAPI
EXPOSE 8000

# 7. Lancer le serveur Uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]