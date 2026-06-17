import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_TOKEN = os.getenv("API_TOKEN")
    PORT      = int(os.getenv("PORT", "8000"))

    if not API_TOKEN:
        raise RuntimeError(
            "Variable d'environnement API_TOKEN manquante. "
            "Ajoutez API_TOKEN=<votre_token> dans exercice2_graphql/.env"
        )
