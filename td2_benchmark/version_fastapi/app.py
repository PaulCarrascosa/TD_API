#!/usr/bin/env python3
"""API REST - Carnet de contacts (FastAPI)"""

from fastapi import FastAPI, HTTPException, Header, Query, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, List

app = FastAPI(title="API Contacts")
API_TOKEN = "mon_token_secret_123"


class ContactInput(BaseModel):
    nom: str
    email: EmailStr
    telephone: Optional[str] = None
    favori: bool = False


class Contact(ContactInput):
    id: int


contacts_db: List[dict] = [
    {"id": 1, "nom": "Aïcha Diallo", "email": "aicha@exemple.fr",
     "telephone": "0601020304", "favori": True},
]
next_id = 2


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


@app.get("/contacts")
def get_contacts(
    favori: Optional[bool] = Query(None),
    _: None = Depends(verifier_token),
):
    resultats = contacts_db
    if favori is not None:
        resultats = [c for c in contacts_db if c["favori"] == favori]
    return {"contacts": resultats, "total": len(resultats)}


@app.get("/contacts/{contact_id}")
def get_contact(contact_id: int, _: None = Depends(verifier_token)):
    contact = next((c for c in contacts_db if c["id"] == contact_id), None)
    if contact is None:
        raise HTTPException(status_code=404,
                            detail=f"Aucun contact avec l'id {contact_id}")
    return contact


@app.post("/contacts", status_code=201)
def create_contact(data: ContactInput, _: None = Depends(verifier_token)):
    global next_id
    nouveau = {
        "id":        next_id,
        "nom":       data.nom.strip(),
        "email":     data.email,
        "telephone": data.telephone,
        "favori":    data.favori,
    }
    contacts_db.append(nouveau)
    next_id += 1
    return nouveau


@app.put("/contacts/{contact_id}")
def update_contact(contact_id: int, data: ContactInput,
                   _: None = Depends(verifier_token)):
    contact = next((c for c in contacts_db if c["id"] == contact_id), None)
    if contact is None:
        raise HTTPException(status_code=404,
                            detail=f"Aucun contact avec l'id {contact_id}")
    contact["nom"]       = data.nom.strip()
    contact["email"]     = data.email
    contact["telephone"] = data.telephone
    contact["favori"]    = data.favori
    return contact


@app.delete("/contacts/{contact_id}", status_code=204)
def delete_contact(contact_id: int, _: None = Depends(verifier_token)):
    global contacts_db
    contact = next((c for c in contacts_db if c["id"] == contact_id), None)
    if contact is None:
        raise HTTPException(status_code=404,
                            detail=f"Aucun contact avec l'id {contact_id}")
    contacts_db[:] = [c for c in contacts_db if c["id"] != contact_id]


if __name__ == "__main__":
    import uvicorn
    print("=== API Contacts (FastAPI) démarrée sur http://localhost:8000 ===")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
