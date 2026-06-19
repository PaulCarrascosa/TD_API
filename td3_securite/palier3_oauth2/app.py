#!/usr/bin/env python3
"""Palier 3 - OAuth2 simplifié (Authorization Code Flow)

Flux implémenté :
  1. Client → POST /oauth/authorize  (username, password, client_id)
             ← { authorization_code }   (valable 60 s, usage unique)

  2. Client → POST /oauth/token  (code, client_id, client_secret)
             ← { access_token (JWT 15 min), refresh_token (7 jours) }

  3. Client → POST /oauth/refresh  (refresh_token)
             ← { access_token (JWT 15 min renouvelé) }

  4. Client → GET /profil  Header: Authorization: Bearer <access_token>
             ← { utilisateur }

Sécurités :
  - Le code d'autorisation est à usage unique et expire après 60 secondes.
  - Le code est supprimé dès qu'il est échangé (replay attack impossible).
  - Le refresh_token est une chaîne aléatoire non-JWT, stockée en mémoire
    avec expiration ; il peut être révoqué explicitement.
"""
from flask import Flask, jsonify, request, abort
from jose import jwt, JWTError
import secrets
from datetime import datetime, timedelta

app = Flask(__name__)

SECRET_KEY = "a-changer-en-production"
ALGORITHM = "HS256"
DUREE_ACCESS_MINUTES = 15
DUREE_REFRESH_JOURS = 7
DUREE_CODE_SECONDES = 60

utilisateurs_db = {
    "alice": "motdepasse123",
    "bob": "secret456",
}

clients_db = {
    "comparateur-prix": "secret-comparateur",
    "app-mobile": "secret-mobile",
}

# { code: {"user": str, "expire_le": datetime} }
codes_autorisation = {}

# { token: {"user": str, "expire_le": datetime} }
refresh_tokens = {}


def creer_access_token(username):
    payload = {
        "sub": username,
        "exp": datetime.utcnow() + timedelta(minutes=DUREE_ACCESS_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verifier_access_token():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        abort(401, description="Token manquant")
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except JWTError:
        abort(401, description="Token invalide ou expiré")


@app.errorhandler(400)
def bad_request(e):
    return jsonify({"erreur": "Requête invalide", "detail": str(e.description)}), 400

@app.errorhandler(401)
def unauthorized(e):
    return jsonify({"erreur": "Non autorisé", "detail": str(e.description)}), 401


@app.route("/oauth/authorize", methods=["POST"])
def authorize():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    client_id = data.get("client_id")

    if username not in utilisateurs_db or utilisateurs_db[username] != password:
        abort(401, description="Identifiants utilisateur invalides")
    if client_id not in clients_db:
        abort(401, description="client_id inconnu")

    code = secrets.token_hex(16)
    codes_autorisation[code] = {
        "user": username,
        "expire_le": datetime.utcnow() + timedelta(seconds=DUREE_CODE_SECONDES),
    }
    return jsonify({"authorization_code": code}), 200


@app.route("/oauth/token", methods=["POST"])
def token():
    data = request.get_json() or {}
    code = data.get("code")
    client_id = data.get("client_id")
    client_secret = data.get("client_secret")

    if client_id not in clients_db or clients_db[client_id] != client_secret:
        abort(401, description="client_id ou client_secret invalide")

    if code not in codes_autorisation:
        abort(400, description="Code d'autorisation invalide")

    infos = codes_autorisation.pop(code)

    if datetime.utcnow() > infos["expire_le"]:
        abort(400, description="Code d'autorisation expiré")

    username = infos["user"]
    access_token = creer_access_token(username)
    refresh_token = secrets.token_hex(32)
    refresh_tokens[refresh_token] = {
        "user": username,
        "expire_le": datetime.utcnow() + timedelta(days=DUREE_REFRESH_JOURS),
    }

    return jsonify({
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": DUREE_ACCESS_MINUTES * 60,
        "refresh_token": refresh_token,
    }), 200


@app.route("/oauth/refresh", methods=["POST"])
def refresh():
    data = request.get_json() or {}
    refresh_token = data.get("refresh_token")

    if refresh_token not in refresh_tokens:
        abort(401, description="Refresh token invalide")

    infos = refresh_tokens[refresh_token]
    if datetime.utcnow() > infos["expire_le"]:
        del refresh_tokens[refresh_token]
        abort(401, description="Refresh token expiré")

    access_token = creer_access_token(infos["user"])
    return jsonify({
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": DUREE_ACCESS_MINUTES * 60,
    }), 200


@app.route("/profil", methods=["GET"])
def profil():
    username = verifier_access_token()
    return jsonify({"utilisateur": username}), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5003)
