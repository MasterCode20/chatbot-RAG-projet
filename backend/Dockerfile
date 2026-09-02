FROM python:3.12-slim

WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Copier et installer les requirements du backend
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Exposer le port FastAPI
EXPOSE 8000

# Commande de lancement (en ciblant le module backend.main:app depuis la racine)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]