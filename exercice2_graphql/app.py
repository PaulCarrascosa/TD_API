import logging
from fastapi import FastAPI, Depends, HTTPException, Request
from strawberry.fastapi import GraphQLRouter
from config import Config
from schema import schema

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

API_TOKEN = Config.API_TOKEN

# Authentification — dépendance FastAPI (même logique qu'en REST)
async def verifier_token(request: Request):
    """Vérifie le Bearer token sur les requêtes POST (les vraies requêtes GraphQL).
    Les GET ne sont pas vérifiés pour permettre l'ouverture du playground GraphiQL."""
    if request.method != "POST":
        return
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Format attendu : Bearer <token>")
    token = authorization.split(" ")[1]
    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Token invalide ou expiré")

# Application FastAPI + routeur GraphQL Strawberry
app = FastAPI(
    title="API GraphQL - Livres",
    description="Exemple guidé — module ECHE834",
    version="1.0.0",
)

# Le GraphQLRouter expose :
#  - POST /graphql  → exécution des requêtes GraphQL
#  - GET  /graphql  → playground GraphiQL interactif (navigateur)
graphql_router = GraphQLRouter(
    schema,
    dependencies=[Depends(verifier_token)],
)
app.include_router(graphql_router, prefix="/graphql")

@app.get("/")
async def root():
    return {
        "message": "API GraphQL opérationnelle",
        "playground": "/graphql",
        "docs":        "/docs",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
