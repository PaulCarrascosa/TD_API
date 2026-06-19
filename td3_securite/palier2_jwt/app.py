#!/usr/bin/env python3
"""Palier 2 - Authentification par JWT

Question 4.4 — Révocation d'un JWT avant expiration naturelle :
Un JWT étant auto-porté, le serveur ne le stocke pas et ne peut donc pas
le "supprimer". Pour invalider un JWT avant son expiration, deux approches
existent : (1) maintenir côté serveur une liste noire (jti blacklist) des
identifiants de tokens révoqués, vérifiée à chaque requête — ce qui
réintroduit un état serveur ; (2) réduire la durée de vie du token (ex. 5 min)
pour limiter la fenêtre d'utilisation en cas de vol, et utiliser un refresh
token de longue durée pour réémettre silencieusement des access tokens
(stratégie implémentée au palier 3).
"""
from flask import Flask, jsonify, request, abort
from jose import jwt, JWTError
from datetime import datetime, timedelta

app = Flask(__name__)

SECRET_KEY = "a-changer-en-production"
ALGORITHM = "HS256"
DUREE_TOKEN_MINUTES = 30

utilisateurs_db = {
    "alice": "motdepasse123",
    "bob": "secret456",
}


def creer_jwt(username):
    payload = {
        "sub": username,
        "exp": datetime.utcnow() + timedelta(minutes=DUREE_TOKEN_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verifier_jwt():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        abort(401, description="Token manquant")
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except JWTError:
        abort(401, description="Token invalide ou expiré")


@app.errorhandler(401)
def unauthorized(e):
    return jsonify({"erreur": "Non autorisé", "detail": str(e.description)}), 401


@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    if username not in utilisateurs_db or utilisateurs_db[username] != password:
        abort(401, description="Identifiants invalides")
    return jsonify({"access_token": creer_jwt(username), "token_type": "bearer"}), 200


@app.route("/profil", methods=["GET"])
def profil():
    username = verifier_jwt()
    return jsonify({"utilisateur": username}), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5002)
