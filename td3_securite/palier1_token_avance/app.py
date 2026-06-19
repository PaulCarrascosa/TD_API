#!/usr/bin/env python3
"""Palier 1 - Token avec expiration et révocation"""
from flask import Flask, jsonify, request, abort
import secrets
from datetime import datetime, timedelta

app = Flask(__name__)

utilisateurs_db = {
    "alice": "motdepasse123",
    "bob": "secret456",
}

tokens_actifs = {}
DUREE_TOKEN_MINUTES = 30


def generer_token(username):
    token = secrets.token_hex(32)
    tokens_actifs[token] = {
        "user": username,
        "expire_le": datetime.utcnow() + timedelta(minutes=DUREE_TOKEN_MINUTES),
    }
    return token


def verifier_token():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        abort(401, description="Token manquant")
    token = auth_header.split(" ")[1]
    if token not in tokens_actifs:
        abort(403, description="Token invalide")
    infos = tokens_actifs[token]
    if datetime.utcnow() > infos["expire_le"]:
        del tokens_actifs[token]
        abort(401, description="Token expiré")
    return infos["user"]


@app.errorhandler(400)
def bad_request(e):
    return jsonify({"erreur": "Requête invalide", "detail": str(e.description)}), 400

@app.errorhandler(401)
def unauthorized(e):
    return jsonify({"erreur": "Non autorisé", "detail": str(e.description)}), 401

@app.errorhandler(403)
def forbidden(e):
    return jsonify({"erreur": "Accès refusé", "detail": str(e.description)}), 403


@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    if username not in utilisateurs_db or utilisateurs_db[username] != password:
        abort(401, description="Identifiants invalides")
    token = generer_token(username)
    return jsonify({"token": token, "expire_dans_minutes": DUREE_TOKEN_MINUTES}), 200


@app.route("/auth/logout", methods=["POST"])
def logout():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.split(" ")[1] if " " in auth_header else None
    if token and token in tokens_actifs:
        del tokens_actifs[token]
    return "", 204


@app.route("/profil", methods=["GET"])
def profil():
    username = verifier_token()
    return jsonify({"utilisateur": username}), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
