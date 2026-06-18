import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from starlette.testclient import TestClient
import app as app_module
from app import app

TOKEN      = "mon_token_secret_123"
HEADERS_OK = {"Authorization": f"Bearer {TOKEN}"}
HEADERS_BAD = {"Authorization": "Bearer mauvais_token"}


@pytest.fixture(autouse=True)
def reset_db():
    """Réinitialise la base de données avant chaque test."""
    app_module.salles_db[:] = [
        {"id": 1, "nom": "Salle Voltaire", "capacite": 12,
         "equipement": ["vidéoprojecteur", "tableau blanc"]},
        {"id": 2, "nom": "Salle Curie", "capacite": 6,
         "equipement": ["écran TV"]},
    ]
    app_module.reservations_db[:] = [
        {"id": 1, "salle_id": 1, "usager": "M. Dupont",
         "date": "2026-06-20", "heure_debut": "14:00", "heure_fin": "15:30"},
    ]
    app_module.next_reservation_id = 2


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# ─── Tests GET /salles ────────────────────────────────────────────────────────

class TestGetSalles:
    def test_lister_salles(self, client):
        """GET /salles → 200 et liste non vide."""
        r = client.get("/salles", headers=HEADERS_OK)
        assert r.status_code == 200
        data = r.json()
        assert "salles" in data
        assert data["total"] >= 1

    def test_lister_salles_sans_token(self, client):
        """GET /salles sans token → 401."""
        r = client.get("/salles")
        assert r.status_code == 401

    def test_lister_salles_mauvais_token(self, client):
        """GET /salles avec mauvais token → 403."""
        r = client.get("/salles", headers=HEADERS_BAD)
        assert r.status_code == 403


# ─── Tests POST /salles/{id}/reservations ─────────────────────────────────────

class TestCreateReservation:
    def test_creer_reservation_valide(self, client):
        """POST réservation valide → 201."""
        payload = {
            "usager": "Mme Martin",
            "date": "2026-07-01",
            "heure_debut": "09:00",
            "heure_fin": "10:30",
        }
        r = client.post("/salles/1/reservations", json=payload, headers=HEADERS_OK)
        assert r.status_code == 201
        data = r.json()
        assert data["usager"] == "Mme Martin"
        assert "id" in data

    def test_creer_reservation_chevauchement(self, client):
        """POST sur créneau déjà pris (même salle, même date, chevauchement) → 409."""
        payload = {
            "usager": "Mme Durand",
            "date": "2026-06-20",
            "heure_debut": "15:00",   # chevauche 14:00-15:30
            "heure_fin": "16:00",
        }
        r = client.post("/salles/1/reservations", json=payload, headers=HEADERS_OK)
        assert r.status_code == 409

    def test_creer_reservation_salle_inexistante(self, client):
        """POST sur salle inexistante → 404."""
        payload = {
            "usager": "M. Test",
            "date": "2026-07-01",
            "heure_debut": "10:00",
            "heure_fin": "11:00",
        }
        r = client.post("/salles/999/reservations", json=payload, headers=HEADERS_OK)
        assert r.status_code == 404

    def test_creer_reservation_champ_manquant(self, client):
        """POST sans champ obligatoire (date) → 422 (validation Pydantic)."""
        payload = {
            "usager": "M. Test",
            "heure_debut": "10:00",
            "heure_fin": "11:00",
        }
        r = client.post("/salles/1/reservations", json=payload, headers=HEADERS_OK)
        assert r.status_code == 422

    def test_pas_de_chevauchement_autre_date(self, client):
        """POST même créneau horaire mais date différente → 201."""
        payload = {
            "usager": "Mme Petit",
            "date": "2026-06-21",     # jour différent
            "heure_debut": "14:00",
            "heure_fin": "15:30",
        }
        r = client.post("/salles/1/reservations", json=payload, headers=HEADERS_OK)
        assert r.status_code == 201

    def test_pas_de_chevauchement_autre_salle(self, client):
        """POST même créneau mais salle différente → 201."""
        payload = {
            "usager": "M. Bernard",
            "date": "2026-06-20",
            "heure_debut": "14:00",
            "heure_fin": "15:30",
        }
        r = client.post("/salles/2/reservations", json=payload, headers=HEADERS_OK)
        assert r.status_code == 201


# ─── Tests DELETE /reservations/{id} ─────────────────────────────────────────

class TestDeleteReservation:
    def test_annuler_reservation_existante(self, client):
        """DELETE réservation existante → 204."""
        r = client.delete("/reservations/1", headers=HEADERS_OK)
        assert r.status_code == 204

    def test_annuler_reservation_inexistante(self, client):
        """DELETE réservation inexistante → 404."""
        r = client.delete("/reservations/999", headers=HEADERS_OK)
        assert r.status_code == 404


# ─── Tests GET /salles/{id}/reservations ─────────────────────────────────────

class TestGetReservations:
    def test_lister_reservations_salle(self, client):
        """GET réservations d'une salle existante → 200."""
        r = client.get("/salles/1/reservations", headers=HEADERS_OK)
        assert r.status_code == 200
        data = r.json()
        assert "reservations" in data
        assert data["total"] == 1

    def test_lister_reservations_salle_inexistante(self, client):
        """GET réservations d'une salle inexistante → 404."""
        r = client.get("/salles/999/reservations", headers=HEADERS_OK)
        assert r.status_code == 404
