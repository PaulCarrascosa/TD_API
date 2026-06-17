import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_TOKEN = os.getenv("API_TOKEN")
    DEBUG     = os.getenv("DEBUG", "False").lower() == "true"
    PORT      = int(os.getenv("PORT", "5000"))

    # Vérification au démarrage : l'application ne démarre pas sans token
    if not API_TOKEN:
        raise RuntimeError(
            "Variable d'environnement API_TOKEN manquante. "
            "Ajoutez API_TOKEN=<votre_token> dans exercice1_rest/.env"
        )
