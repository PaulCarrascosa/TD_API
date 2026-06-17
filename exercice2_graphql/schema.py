import strawberry
from typing import Optional, List

# TYPES GraphQL
@strawberry.type
class Evenement:
    """Représente un événement dans notre système."""
    id:           int
    nom:          str
    lieu:         str
    date:         str
    capacite_max: int
    organisateur: str

@strawberry.input
class EvenementInput:
    """Données d'entrée pour créer ou modifier un événement."""
    nom:          str
    lieu:         str
    date:         str
    capacite_max: int
    organisateur: str

@strawberry.type
class DeleteResult:
    """Résultat d'une suppression."""
    success: bool
    message: str

# BASE DE DONNÉES EN MÉMOIRE
evenements_db: List[dict] = [
    {"id": 1, "nom": "Conférence Python", "lieu": "Paris",    "date": "2025-09-01", "capacite_max": 200, "organisateur": "PyFrance"},
    {"id": 2, "nom": "Hackathon IA",      "lieu": "Lyon",     "date": "2025-10-15", "capacite_max": 100, "organisateur": "AI Club"},
    {"id": 3, "nom": "Workshop Docker",   "lieu": "Bordeaux", "date": "2025-11-20", "capacite_max": 50,  "organisateur": "DevOps Sud"},
]
_next_id = 4

def dict_to_evenement(d: dict) -> Evenement:
    return Evenement(
        id=d["id"], nom=d["nom"], lieu=d["lieu"],
        date=d["date"], capacite_max=d["capacite_max"],
        organisateur=d["organisateur"],
    )

def valider_evenement_input(data: EvenementInput) -> None:
    """Lève une ValueError si les données sont invalides."""
    if not data.nom.strip():
        raise ValueError("Le nom ne peut pas être vide")
    if not data.lieu.strip():
        raise ValueError("Le lieu ne peut pas être vide")
    if data.capacite_max <= 0:
        raise ValueError("capacite_max doit être un entier strictement positif")

# QUERIES — Lecture (équivalent GET en REST)
@strawberry.type
class Query:
    @strawberry.field(description="Retourne tous les événements (filtre optionnel par lieu)")
    def evenements(self, lieu: Optional[str] = None) -> List[Evenement]:
        if lieu:
            return [dict_to_evenement(e) for e in evenements_db
                    if lieu.lower() in e["lieu"].lower()]
        return [dict_to_evenement(e) for e in evenements_db]

    @strawberry.field(description="Retourne un événement par son identifiant")
    def evenement(self, id: int) -> Optional[Evenement]:
        e = next((e for e in evenements_db if e["id"] == id), None)
        return dict_to_evenement(e) if e else None

# MUTATIONS — Écriture (équivalent POST / PUT / DELETE en REST)
@strawberry.type
class Mutation:
    @strawberry.mutation(description="Crée un nouvel événement")
    def creer_evenement(self, evenement_input: EvenementInput) -> Evenement:
        global _next_id
        valider_evenement_input(evenement_input)
        nouveau = {
            "id":           _next_id,
            "nom":          evenement_input.nom.strip(),
            "lieu":         evenement_input.lieu.strip(),
            "date":         evenement_input.date,
            "capacite_max": evenement_input.capacite_max,
            "organisateur": evenement_input.organisateur.strip(),
        }
        evenements_db.append(nouveau)
        _next_id += 1
        return dict_to_evenement(nouveau)

    @strawberry.mutation(description="Modifie un événement existant")
    def modifier_evenement(self, id: int, evenement_input: EvenementInput) -> Optional[Evenement]:
        e = next((e for e in evenements_db if e["id"] == id), None)
        if e is None:
            return None
        valider_evenement_input(evenement_input)
        e["nom"]          = evenement_input.nom.strip()
        e["lieu"]         = evenement_input.lieu.strip()
        e["date"]         = evenement_input.date
        e["capacite_max"] = evenement_input.capacite_max
        e["organisateur"] = evenement_input.organisateur.strip()
        return dict_to_evenement(e)

    @strawberry.mutation(description="Supprime un événement")
    def supprimer_evenement(self, id: int) -> DeleteResult:
        global evenements_db
        avant = len(evenements_db)
        evenements_db = [e for e in evenements_db if e["id"] != id]
        if len(evenements_db) < avant:
            return DeleteResult(success=True,  message=f"Événement {id} supprimé")
        return DeleteResult(success=False, message=f"Événement {id} introuvable")

# SCHÉMA final
schema = strawberry.Schema(query=Query, mutation=Mutation)
