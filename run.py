#!/usr/bin/env python3
"""
Setup du projet TD API ECHE834
Lance : python run.py
Cree requirements.txt, .env, .gitignore et l'architecture de dossiers.
"""

import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))

# ─── Contenu des fichiers de configuration ───────────────────────────────

REQUIREMENTS = """\
flask==3.0.3
flask-restful==0.3.10
fastapi==0.111.0
uvicorn[standard]==0.30.1
pydantic==2.7.3
strawberry-graphql[fastapi]==0.235.0
pytest==8.2.2
pytest-asyncio==0.23.7
httpx==0.27.0
python-dotenv==1.0.1
requests==2.32.3
pytest-cov==5.0.0
"""

ENV = """\
# Token d'authentification API
API_TOKEN=mon_token_secret_123

# Configuration Flask
FLASK_ENV=development
FLASK_DEBUG=1

# Port de l'application
PORT=5000
"""

GITIGNORE = """\
venv/
.env
__pycache__/
*.pyc
.pytest_cache/
api.log
*.egg-info/
dist/
.coverage
"""

# ─── Helpers ─────────────────────────────────────────────────────────────

def creer_fichier(chemin_relatif, contenu):
    """Cree un fichier avec son contenu."""
    chemin = os.path.join(BASE, chemin_relatif)
    repertoire = os.path.dirname(chemin)
    if repertoire:
        os.makedirs(repertoire, exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(contenu)

def creer_dossier(chemin_relatif):
    """Cree un dossier et son __init__.py."""
    chemin = os.path.join(BASE, chemin_relatif)
    os.makedirs(chemin, exist_ok=True)
    init = os.path.join(chemin, "__init__.py")
    if not os.path.exists(init):
        open(init, "w").close()

# ─── Main ────────────────────────────────────────────────────────────────

def main():
    creer_fichier("requirements.txt", REQUIREMENTS)
    creer_fichier(".env", ENV)
    creer_fichier(".gitignore", GITIGNORE)

    # Exercice 1 — REST Flask
    creer_dossier("exercice1_rest")
    creer_dossier("exercice1_rest/tests")
    # Exercice 2 — GraphQL Strawberry
    creer_dossier("exercice2_graphql")
    creer_dossier("exercice2_graphql/tests")
    # Docker
    creer_dossier("docker")

    res = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r",
         os.path.join(BASE, "requirements.txt")],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
