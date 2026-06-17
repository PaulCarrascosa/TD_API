from flask import Flask, jsonify, request, abort
import logging
import time
from config import Config

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialisation de l'application Flask
app = Flask(__name__)
API_TOKEN = Config.API_TOKEN

@app.before_request
def before_request():
    request._start_time = time.time()
    logger.info(f"→ {request.method} {request.path}")

@app.after_request
def after_request(response):
    duration = round((time.time() - request._start_time) * 1000, 2)
    logger.info(f"← {response.status_code} [{duration}ms]")
    return response

# Base de données
evenements_db = [
    {"id": 1, "nom": "Conférence Python", "lieu": "Paris",    "date": "2025-09-01", "capacite_max": 200, "organisateur": "PyFrance"},
    {"id": 2, "nom": "Hackathon IA",      "lieu": "Lyon",     "date": "2025-10-15", "capacite_max": 100, "organisateur": "AI Club"},
    {"id": 3, "nom": "Workshop Docker",   "lieu": "Bordeaux", "date": "2025-11-20", "capacite_max": 50,  "organisateur": "DevOps Sud"},
]
next_id = 4  # Compteur pour les nouveaux IDs

# Vérification du token d'authentification
def verifier_token():
    """Vérifie que le token Bearer est présent et valide."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        abort(401, description="Token manquant. Format attendu: Bearer <token>")
    token = auth_header.split(" ")[1]
    if token != API_TOKEN:
        abort(403, description="Token invalide ou expiré")

# VALIDATION des données d'entrée
def valider_evenement(data, required_fields=None):
    """Valide les données d'un événement. Retourne (True, None) ou (False, message)."""
    if required_fields is None:
        required_fields = ["nom", "lieu", "date", "capacite_max", "organisateur"]
    for champ in required_fields:
        if champ not in data:
            return False, f"Champ obligatoire manquant : {champ}"
    if "capacite_max" in data:
        if not isinstance(data["capacite_max"], int) or data["capacite_max"] <= 0:
            return False, "capacite_max doit être un entier strictement positif"
    if "nom" in data and len(data["nom"].strip()) == 0:
        return False, "Le nom ne peut pas être vide"
    return True, None

# GESTION DES ERREURS
@app.errorhandler(400)
def bad_request(e):
    return jsonify({"erreur": "Requête invalide", "detail": str(e.description)}), 400

@app.errorhandler(401)
def unauthorized(e):
    return jsonify({"erreur": "Non autorisé", "detail": str(e.description)}), 401

@app.errorhandler(403)
def forbidden(e):
    return jsonify({"erreur": "Accès refusé", "detail": str(e.description)}), 403

@app.errorhandler(404)
def not_found(e):
    return jsonify({"erreur": "Ressource introuvable", "detail": str(e.description)}), 404

# ROUTES — Endpoints CRUD
# GET /evenements — Récupérer tous les événements
@app.route("/evenements", methods=["GET"])
def get_evenements():
    """Retourne la liste complète des événements."""
    verifier_token()
    # Paramètre de filtre optionnel : ?lieu=Paris
    lieu_filtre = request.args.get("lieu")
    if lieu_filtre:
        resultats = [e for e in evenements_db if lieu_filtre.lower() in e["lieu"].lower()]
        return jsonify({"evenements": resultats, "total": len(resultats)}), 200
    return jsonify({"evenements": evenements_db, "total": len(evenements_db)}), 200

# GET /evenements/<id> — Récupérer un événement par son ID
@app.route("/evenements/<int:event_id>", methods=["GET"])
def get_evenement(event_id):
    """Retourne un événement spécifique par son identifiant."""
    verifier_token()
    evenement = next((e for e in evenements_db if e["id"] == event_id), None)
    if evenement is None:
        abort(404, description=f"Aucun événement avec l'id {event_id}")
    return jsonify(evenement), 200

# POST /evenements — Créer un nouvel événement
@app.route("/evenements", methods=["POST"])
def create_evenement():
    """Crée un nouvel événement dans la base de données."""
    global next_id
    verifier_token()
    # Vérification du Content-Type
    if not request.is_json:
        abort(400, description="Le corps de la requête doit être en JSON")
    data = request.get_json()
    valide, message = valider_evenement(data)
    if not valide:
        abort(400, description=message)
    nouvel_evenement = {
        "id":           next_id,
        "nom":          data["nom"].strip(),
        "lieu":         data["lieu"].strip(),
        "date":         data["date"],
        "capacite_max": data["capacite_max"],
        "organisateur": data["organisateur"].strip(),
    }
    evenements_db.append(nouvel_evenement)
    next_id += 1
    # HTTP 201 Created — Bonne pratique REST
    return jsonify(nouvel_evenement), 201

# PUT /evenements/<id> — Mettre à jour un événement
@app.route("/evenements/<int:event_id>", methods=["PUT"])
def update_evenement(event_id):
    """Met à jour un événement existant (remplacement complet)."""
    verifier_token()
    evenement = next((e for e in evenements_db if e["id"] == event_id), None)
    if evenement is None:
        abort(404, description=f"Aucun événement avec l'id {event_id}")
    if not request.is_json:
        abort(400, description="Le corps de la requête doit être en JSON")
    data = request.get_json()
    valide, message = valider_evenement(data)
    if not valide:
        abort(400, description=message)
    evenement["nom"]          = data["nom"].strip()
    evenement["lieu"]         = data["lieu"].strip()
    evenement["date"]         = data["date"]
    evenement["capacite_max"] = data["capacite_max"]
    evenement["organisateur"] = data["organisateur"].strip()
    return jsonify(evenement), 200

# DELETE /evenements/<id> — Supprimer un événement
@app.route("/evenements/<int:event_id>", methods=["DELETE"])
def delete_evenement(event_id):
    """Supprime un événement de la base de données."""
    global evenements_db
    verifier_token()
    evenement = next((e for e in evenements_db if e["id"] == event_id), None)
    if evenement is None:
        abort(404, description=f"Aucun événement avec l'id {event_id}")
    evenements_db = [e for e in evenements_db if e["id"] != event_id]
    # HTTP 204 No Content — Bonne pratique REST pour DELETE
    return "", 204

if __name__ == "__main__":
    print("=== API Événements démarrée sur http://localhost:5000 ===")
    app.run(debug=True, host="0.0.0.0", port=5000)
