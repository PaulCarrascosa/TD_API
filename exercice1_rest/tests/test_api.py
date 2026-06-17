import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import app, evenements_db, next_id

TOKEN       = "mon_token_secret_123"
HEADERS_OK  = {"Authorization": f"Bearer {TOKEN}"}
HEADERS_BAD = {"Authorization": "Bearer mauvais_token"}

@pytest.fixture(autouse=True)
def reset_db():
    # Réinitialise la base de données avant chaque test pour éviter les effets de bord
    import app as app_module
    app_module.evenements_db = [
        {"id": 1, "nom": "Conférence Python", "lieu": "Paris",    "date": "2025-09-01", "capacite_max": 200, "organisateur": "PyFrance"},
        {"id": 2, "nom": "Hackathon IA",      "lieu": "Lyon",     "date": "2025-10-15", "capacite_max": 100, "organisateur": "AI Club"},
        {"id": 3, "nom": "Workshop Docker",   "lieu": "Bordeaux", "date": "2025-11-20", "capacite_max": 50,  "organisateur": "DevOps Sud"},
    ]
    app_module.next_id = 4

@pytest.fixture
def client():
    """Fixture : crée un client de test Flask."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

# ─── Tests GET ─────────────────────────────────────────────────────────────
class TestGetEvenements:
    def test_get_tous_les_evenements(self, client):
        """GET /evenements → 200 + liste non vide."""
        r = client.get("/evenements", headers=HEADERS_OK)
        assert r.status_code == 200
        data = r.get_json()
        assert "evenements" in data
        assert data["total"] >= 3

    def test_get_evenement_par_id(self, client):
        """GET /evenements/1 → 200 + nom correct."""
        r = client.get("/evenements/1", headers=HEADERS_OK)
        assert r.status_code == 200
        assert r.get_json()["nom"] == "Conférence Python"

    def test_get_evenement_inexistant(self, client):
        """GET /evenements/999 → 404."""
        r = client.get("/evenements/999", headers=HEADERS_OK)
        assert r.status_code == 404

    def test_get_sans_token(self, client):
        """GET /evenements sans token → 401."""
        r = client.get("/evenements")
        assert r.status_code == 401

    def test_get_mauvais_token(self, client):
        """GET /evenements avec mauvais token → 403."""
        r = client.get("/evenements", headers=HEADERS_BAD)
        assert r.status_code == 403

    def test_filtre_par_lieu(self, client):
        """GET /evenements?lieu=Paris → résultats filtrés."""
        r = client.get("/evenements?lieu=Paris", headers=HEADERS_OK)
        assert r.status_code == 200
        data = r.get_json()
        assert data["total"] == 1
        assert data["evenements"][0]["lieu"] == "Paris"

# ─── Tests POST ────────────────────────────────────────────────────────────
class TestCreateEvenement:
    def test_creer_evenement_valide(self, client):
        """POST /evenements avec données valides → 201."""
        payload = {"nom": "Summit Tech", "lieu": "Nantes",
                   "date": "2025-12-01", "capacite_max": 300,
                   "organisateur": "TechNantes"}
        r = client.post("/evenements", json=payload, headers=HEADERS_OK)
        assert r.status_code == 201
        ev = r.get_json()
        assert ev["nom"] == "Summit Tech"
        assert "id" in ev

    def test_creer_evenement_champ_manquant(self, client):
        """POST /evenements sans lieu → 400."""
        payload = {"nom": "Ev", "date": "2025-12-01",
                   "capacite_max": 50, "organisateur": "Org"}
        r = client.post("/evenements", json=payload, headers=HEADERS_OK)
        assert r.status_code == 400

    def test_creer_evenement_capacite_invalide(self, client):
        """POST /evenements avec capacite_max négative → 400."""
        payload = {"nom": "Ev", "lieu": "Paris", "date": "2025-12-01",
                   "capacite_max": -10, "organisateur": "Org"}
        r = client.post("/evenements", json=payload, headers=HEADERS_OK)
        assert r.status_code == 400

# ─── Tests DELETE ──────────────────────────────────────────────────────────
class TestDeleteEvenement:
    def test_supprimer_evenement(self, client):
        """DELETE /evenements/1 → 204."""
        r = client.delete("/evenements/1", headers=HEADERS_OK)
        assert r.status_code == 204

    def test_supprimer_evenement_inexistant(self, client):
        """DELETE /evenements/999 → 404."""
        r = client.delete("/evenements/999", headers=HEADERS_OK)
        assert r.status_code == 404
