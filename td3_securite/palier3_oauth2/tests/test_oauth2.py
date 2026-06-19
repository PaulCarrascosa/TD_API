import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest
from app import app as flask_app, codes_autorisation, refresh_tokens

CLIENT_ID = "comparateur-prix"
CLIENT_SECRET = "secret-comparateur"


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def reset_state():
    codes_autorisation.clear()
    refresh_tokens.clear()
    yield
    codes_autorisation.clear()
    refresh_tokens.clear()


def obtenir_code(client, username="alice", password="motdepasse123"):
    r = client.post("/oauth/authorize", json={
        "username": username,
        "password": password,
        "client_id": CLIENT_ID,
    })
    return r.get_json()["authorization_code"]


def obtenir_tokens(client):
    code = obtenir_code(client)
    r = client.post("/oauth/token", json={
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    })
    return r.get_json()


# ─── Tests /oauth/authorize ───────────────────────────────────────────────────

def test_authorize_identifiants_valides(client):
    r = client.post("/oauth/authorize", json={
        "username": "alice", "password": "motdepasse123", "client_id": CLIENT_ID,
    })
    assert r.status_code == 200
    assert "authorization_code" in r.get_json()


def test_authorize_identifiants_invalides(client):
    r = client.post("/oauth/authorize", json={
        "username": "alice", "password": "mauvais", "client_id": CLIENT_ID,
    })
    assert r.status_code == 401


def test_authorize_client_inconnu(client):
    r = client.post("/oauth/authorize", json={
        "username": "alice", "password": "motdepasse123", "client_id": "inconnu",
    })
    assert r.status_code == 401


# ─── Tests /oauth/token ───────────────────────────────────────────────────────

def test_token_echange_code_valide(client):
    tokens = obtenir_tokens(client)
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["access_token"].count(".") == 2


def test_token_code_usage_unique(client):
    code = obtenir_code(client)
    client.post("/oauth/token", json={
        "code": code, "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
    })
    r = client.post("/oauth/token", json={
        "code": code, "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
    })
    assert r.status_code == 400


def test_token_client_secret_invalide(client):
    code = obtenir_code(client)
    r = client.post("/oauth/token", json={
        "code": code, "client_id": CLIENT_ID, "client_secret": "mauvais",
    })
    assert r.status_code == 401


# ─── Tests /oauth/refresh ─────────────────────────────────────────────────────

def test_refresh_token_valide(client):
    tokens = obtenir_tokens(client)
    r = client.post("/oauth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200
    assert "access_token" in r.get_json()


def test_refresh_token_invalide(client):
    r = client.post("/oauth/refresh", json={"refresh_token": "faux"})
    assert r.status_code == 401


# ─── Tests /profil ────────────────────────────────────────────────────────────

def test_profil_avec_access_token_valide(client):
    tokens = obtenir_tokens(client)
    r = client.get("/profil", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert r.status_code == 200
    assert r.get_json()["utilisateur"] == "alice"


def test_profil_sans_token(client):
    r = client.get("/profil")
    assert r.status_code == 401
