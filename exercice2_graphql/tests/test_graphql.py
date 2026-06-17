import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from fastapi.testclient import TestClient
from app import app
import schema as schema_module

TOKEN       = "mon_token_secret_123"
HEADERS_OK  = {"Authorization": f"Bearer {TOKEN}"}
HEADERS_BAD = {"Authorization": "Bearer mauvais_token"}
GQL         = "/graphql"

# Helper — envoie une requête GraphQL
def gql(client, query, headers=None):
    """Raccourci pour envoyer une requête GraphQL au serveur de test."""
    return client.post(GQL, json={"query": query}, headers=headers or HEADERS_OK)

# Fixtures
@pytest.fixture(autouse=True)
def reset_db():
    """Réinitialise la base de données avant chaque test."""
    schema_module.evenements_db = [
        {"id": 1, "nom": "Conférence Python", "lieu": "Paris",    "date": "2025-09-01", "capacite_max": 200, "organisateur": "PyFrance"},
        {"id": 2, "nom": "Hackathon IA",      "lieu": "Lyon",     "date": "2025-10-15", "capacite_max": 100, "organisateur": "AI Club"},
        {"id": 3, "nom": "Workshop Docker",   "lieu": "Bordeaux", "date": "2025-11-20", "capacite_max": 50,  "organisateur": "DevOps Sud"},
    ]
    schema_module._next_id = 4

@pytest.fixture
def client():
    """Fixture : crée un client de test FastAPI."""
    with TestClient(app) as c:
        yield c

# Tests QUERY — lecture de données
# Contrairement à REST, tous les appels vont sur POST /graphql
class TestQueryEvenements:
    def test_get_tous_les_evenements(self, client):
        """Query sans filtre → retourne les 3 événements."""
        r = gql(client, "{ evenements { id nom lieu } }")
        assert r.status_code == 200
        assert len(r.json()["data"]["evenements"]) == 3

    def test_get_evenement_par_id(self, client):
        """Query avec id → retourne l'événement correspondant."""
        r = gql(client, "{ evenement(id: 1) { nom lieu } }")
        assert r.status_code == 200
        ev = r.json()["data"]["evenement"]
        assert ev["nom"] == "Conférence Python"
        assert ev["lieu"] == "Paris"

    def test_get_evenement_inexistant(self, client):
        """Query sur un id inexistant → retourne null (pas une erreur HTTP)."""
        r = gql(client, "{ evenement(id: 999) { nom } }")
        assert r.status_code == 200
        assert r.json()["data"]["evenement"] is None

    def test_filtre_par_lieu(self, client):
        """Query avec filtre lieu=Paris → 1 résultat."""
        r = gql(client, '{ evenements(lieu: "Paris") { nom lieu } }')
        assert r.status_code == 200
        data = r.json()["data"]["evenements"]
        assert len(data) == 1
        assert data[0]["lieu"] == "Paris"

    def test_sans_token(self, client):
        """Requête sans token → 401 (rejeté avant même d'atteindre GraphQL)."""
        r = client.post(GQL, json={"query": "{ evenements { nom } }"})
        assert r.status_code == 401

    def test_mauvais_token(self, client):
        """Requête avec mauvais token → 403."""
        r = gql(client, "{ evenements { nom } }", headers=HEADERS_BAD)
        assert r.status_code == 403

# Tests MUTATION — création
class TestMutationCreerEvenement:
    def test_creer_evenement_valide(self, client):
        """Mutation creerEvenement avec données valides → retourne le nouvel événement."""
        r = gql(client, """
            mutation {
              creerEvenement(evenementInput: {
                nom: "Summit Tech"
                lieu: "Nantes"
                date: "2025-12-01"
                capaciteMax: 300
                organisateur: "TechNantes"
              }) { id nom lieu capaciteMax }
            }
        """)
        assert r.status_code == 200
        ev = r.json()["data"]["creerEvenement"]
        assert ev["nom"] == "Summit Tech"
        assert ev["id"] == 4
        assert ev["capaciteMax"] == 300

    def test_creer_evenement_capacite_invalide(self, client):
        """Mutation avec capaciteMax <= 0 → erreur GraphQL (pas 400 HTTP)."""
        r = gql(client, """
            mutation {
              creerEvenement(evenementInput: {
                nom: "Test"
                lieu: "Paris"
                date: "2025-12-01"
                capaciteMax: -5
                organisateur: "Org"
              }) { id }
            }
        """)
        assert r.status_code == 200
        assert "errors" in r.json()

    def test_creer_evenement_nom_vide(self, client):
        """Mutation avec nom vide → erreur GraphQL."""
        r = gql(client, """
            mutation {
              creerEvenement(evenementInput: {
                nom: "   "
                lieu: "Paris"
                date: "2025-12-01"
                capaciteMax: 50
                organisateur: "Org"
              }) { id }
            }
        """)
        assert r.status_code == 200
        assert "errors" in r.json()

# Tests MUTATION — suppression
class TestMutationSupprimerEvenement:
    def test_supprimer_evenement(self, client):
        """Mutation supprimerEvenement sur id existant → success=True."""
        r = gql(client, "mutation { supprimerEvenement(id: 1) { success message } }")
        assert r.status_code == 200
        result = r.json()["data"]["supprimerEvenement"]
        assert result["success"] is True

    def test_supprimer_evenement_inexistant(self, client):
        """Mutation supprimerEvenement sur id inexistant → success=False (pas d'erreur HTTP)."""
        r = gql(client, "mutation { supprimerEvenement(id: 999) { success message } }")
        assert r.status_code == 200
        result = r.json()["data"]["supprimerEvenement"]
        assert result["success"] is False
