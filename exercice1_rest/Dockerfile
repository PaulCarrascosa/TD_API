# ─── Dockerfile — API REST Flask ────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code source
COPY . .

# Exposer le port sur lequel Flask écoute
EXPOSE 5000

# Variables d'environnement (surchargées par docker-compose ou docker run)
ENV FLASK_ENV=production
ENV API_TOKEN=mon_token_secret_123

# Commande de démarrage
CMD ["python", "app.py"]
