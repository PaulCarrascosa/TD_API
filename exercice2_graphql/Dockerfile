# ─── Dockerfile — API GraphQL FastAPI ───────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Exposer le port sur lequel FastAPI/Uvicorn écoute
EXPOSE 8000

# Variable d'environnement
ENV API_TOKEN=mon_token_secret_123

# Uvicorn : serveur ASGI adapté à FastAPI
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
