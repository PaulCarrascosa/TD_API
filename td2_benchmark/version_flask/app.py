#!/usr/bin/env python3
"""API REST - Carnet de contacts (Flask)"""

from flask import Flask, jsonify, request, abort

app = Flask(__name__)
API_TOKEN = "mon_token_secret_123"

contacts_db = [
    {"id": 1, "nom": "Aïcha Diallo", "email": "aicha@exemple.fr",
     "telephone": "0601020304", "favori": True},
]
next_id = 2


def verifier_token():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        abort(401, description="Token manquant. Format attendu: Bearer <token>")
    token = auth_header.split(" ", 1)[1]
    if token != API_TOKEN:
        abort(403, description="Token invalide ou expiré")


def valider_contact(data, required_fields=None):
    if required_fields is None:
        required_fields = ["nom", "email"]
    for champ in required_fields:
        if champ not in data:
            return False, f"Champ obligatoire manquant : {champ}"
    if "nom" in data and len(str(data["nom"]).strip()) == 0:
        return False, "Le nom ne peut pas être vide"
    if "email" in data and "@" not in str(data["email"]):
        return False, "L'email doit contenir '@'"
    return True, None


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


@app.route("/contacts", methods=["GET"])
def get_contacts():
    verifier_token()
    favori_filtre = request.args.get("favori")
    if favori_filtre is not None:
        valeur = favori_filtre.lower() == "true"
        resultats = [c for c in contacts_db if c["favori"] == valeur]
        return jsonify({"contacts": resultats, "total": len(resultats)}), 200
    return jsonify({"contacts": contacts_db, "total": len(contacts_db)}), 200


@app.route("/contacts/<int:contact_id>", methods=["GET"])
def get_contact(contact_id):
    verifier_token()
    contact = next((c for c in contacts_db if c["id"] == contact_id), None)
    if contact is None:
        abort(404, description=f"Aucun contact avec l'id {contact_id}")
    return jsonify(contact), 200


@app.route("/contacts", methods=["POST"])
def create_contact():
    global next_id
    verifier_token()
    if not request.is_json:
        abort(400, description="Le corps de la requête doit être en JSON")
    data = request.get_json()
    valide, message = valider_contact(data)
    if not valide:
        abort(400, description=message)
    nouveau = {
        "id":        next_id,
        "nom":       data["nom"].strip(),
        "email":     data["email"].strip(),
        "telephone": data.get("telephone", None),
        "favori":    bool(data.get("favori", False)),
    }
    contacts_db.append(nouveau)
    next_id += 1
    return jsonify(nouveau), 201


@app.route("/contacts/<int:contact_id>", methods=["PUT"])
def update_contact(contact_id):
    verifier_token()
    contact = next((c for c in contacts_db if c["id"] == contact_id), None)
    if contact is None:
        abort(404, description=f"Aucun contact avec l'id {contact_id}")
    if not request.is_json:
        abort(400, description="Le corps de la requête doit être en JSON")
    data = request.get_json()
    valide, message = valider_contact(data)
    if not valide:
        abort(400, description=message)
    contact["nom"]       = data["nom"].strip()
    contact["email"]     = data["email"].strip()
    contact["telephone"] = data.get("telephone", contact.get("telephone"))
    contact["favori"]    = bool(data.get("favori", contact.get("favori", False)))
    return jsonify(contact), 200


@app.route("/contacts/<int:contact_id>", methods=["DELETE"])
def delete_contact(contact_id):
    global contacts_db
    verifier_token()
    contact = next((c for c in contacts_db if c["id"] == contact_id), None)
    if contact is None:
        abort(404, description=f"Aucun contact avec l'id {contact_id}")
    contacts_db = [c for c in contacts_db if c["id"] != contact_id]
    return "", 204


if __name__ == "__main__":
    print("=== API Contacts (Flask) démarrée sur http://localhost:5000 ===")
    app.run(debug=True, host="0.0.0.0", port=5000)
