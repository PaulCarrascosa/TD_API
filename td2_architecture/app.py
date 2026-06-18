"""API REST - Réservations de salles (médiathèque municipale)"""

from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel, field_validator
from typing import Optional, List

app = FastAPI(
    title="API Réservations de salles — Médiathèque",
    description="Gestion des salles et réservations de la médiathèque municipale",
    version="1.0.0",
)

API_TOKEN = "mon_token_secret_123"

# ─── Base de données en mémoire ───────────────────────────────────────────────

salles_db: List[dict] = [
    {"id": 1, "nom": "Salle Voltaire", "capacite": 12,
     "equipement": ["vidéoprojecteur", "tableau blanc"]},
    {"id": 2, "nom": "Salle Curie", "capacite": 6,
     "equipement": ["écran TV"]},
]

reservations_db: List[dict] = [
    {"id": 1, "salle_id": 1, "usager": "M. Dupont",
     "date": "2026-06-20", "heure_debut": "14:00", "heure_fin": "15:30"},
]

next_salle_id = 3
next_reservation_id = 2


# ─── Schémas Pydantic ─────────────────────────────────────────────────────────

class ReservationInput(BaseModel):
    usager: str
    date: str
    heure_debut: str
    heure_fin: str

    @field_validator("heure_debut", "heure_fin")
    @classmethod
    def format_heure(cls, v: str) -> str:
        parts = v.split(":")
        if len(parts) != 2 or not all(p.isdigit() for p in parts):
            raise ValueError("Format d'heure invalide, attendu HH:MM")
        h, m = int(parts[0]), int(parts[1])
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError("Heure hors plage valide (HH: 0-23, MM: 0-59)")
        return v

    @field_validator("heure_fin")
    @classmethod
    def fin_apres_debut(cls, v: str, info) -> str:
        debut = info.data.get("heure_debut")
        if debut and v <= debut:
            raise ValueError("heure_fin doit être postérieure à heure_debut")
        return v

    @field_validator("date")
    @classmethod
    def format_date(cls, v: str) -> str:
        from datetime import date
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError("Format de date invalide, attendu YYYY-MM-DD")
        return v

    @field_validator("usager")
    @classmethod
    def usager_non_vide(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Le nom de l'usager ne peut pas être vide")
        return v.strip()


# ─── Authentification ─────────────────────────────────────────────────────────

def verifier_token(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401,
                            detail="Token manquant. Format attendu: Bearer <token>")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401,
                            detail="Token manquant. Format attendu: Bearer <token>")
    token = authorization.split(" ", 1)[1]
    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Token invalide ou expiré")


# ─── Logique métier — chevauchement de créneaux ───────────────────────────────

def creneaux_se_chevauchent(debut1: str, fin1: str, debut2: str, fin2: str) -> bool:
    """Retourne True si [debut1, fin1[ et [debut2, fin2[ se superposent."""
    return debut1 < fin2 and debut2 < fin1


# ─── GET /salles ──────────────────────────────────────────────────────────────

@app.get("/salles", summary="Lister toutes les salles")
def get_salles(_: None = Depends(verifier_token)):
    return {"salles": salles_db, "total": len(salles_db)}


# ─── GET /salles/{salle_id}/reservations ──────────────────────────────────────

@app.get("/salles/{salle_id}/reservations",
         summary="Lister les réservations d'une salle")
def get_reservations_salle(salle_id: int, _: None = Depends(verifier_token)):
    salle = next((s for s in salles_db if s["id"] == salle_id), None)
    if salle is None:
        raise HTTPException(
            status_code=404,
            detail=f"Salle {salle_id} introuvable",
        )
    reservations = [r for r in reservations_db if r["salle_id"] == salle_id]
    return {"salle": salle["nom"], "reservations": reservations,
            "total": len(reservations)}


# ─── POST /salles/{salle_id}/reservations ─────────────────────────────────────

@app.post("/salles/{salle_id}/reservations", status_code=201,
          summary="Créer une réservation")
def create_reservation(salle_id: int, data: ReservationInput,
                       _: None = Depends(verifier_token)):
    global next_reservation_id

    salle = next((s for s in salles_db if s["id"] == salle_id), None)
    if salle is None:
        raise HTTPException(
            status_code=404,
            detail=f"Salle {salle_id} introuvable",
        )

    # Contrôle de chevauchement : même salle, même date
    for r in reservations_db:
        if r["salle_id"] == salle_id and r["date"] == data.date:
            if creneaux_se_chevauchent(
                data.heure_debut, data.heure_fin,
                r["heure_debut"], r["heure_fin"],
            ):
                raise HTTPException(
                    status_code=409,
                    detail={
                        "erreur": "Conflit de réservation",
                        "detail": (
                            f"La salle {salle_id} est déjà réservée "
                            f"le {r['date']} de {r['heure_debut']} à {r['heure_fin']}"
                        ),
                    },
                )

    nouvelle = {
        "id":          next_reservation_id,
        "salle_id":    salle_id,
        "usager":      data.usager,
        "date":        data.date,
        "heure_debut": data.heure_debut,
        "heure_fin":   data.heure_fin,
    }
    reservations_db.append(nouvelle)
    next_reservation_id += 1
    return nouvelle


# ─── DELETE /reservations/{reservation_id} ────────────────────────────────────

@app.delete("/reservations/{reservation_id}", status_code=204,
            summary="Annuler une réservation")
def delete_reservation(reservation_id: int, _: None = Depends(verifier_token)):
    global reservations_db
    reservation = next(
        (r for r in reservations_db if r["id"] == reservation_id), None
    )
    if reservation is None:
        raise HTTPException(
            status_code=404,
            detail=f"Réservation {reservation_id} introuvable",
        )
    reservations_db[:] = [r for r in reservations_db if r["id"] != reservation_id]


if __name__ == "__main__":
    import uvicorn
    print("=== API Médiathèque démarrée sur http://localhost:8001 ===")
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)
