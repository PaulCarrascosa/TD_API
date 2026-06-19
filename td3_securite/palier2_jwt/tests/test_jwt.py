import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest
from jose import jwt, JWTError
from datetime import datetime, timedelta
from app import creer_jwt, SECRET_KEY, ALGORITHM


def test_creer_jwt_retourne_structure_trois_parties():
    token = creer_jwt("alice")
    assert token.count(".") == 2


def test_payload_contient_sub():
    token = creer_jwt("alice")
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "alice"


def test_mauvaise_cle_leve_jwterror():
    token = creer_jwt("alice")
    with pytest.raises(JWTError):
        jwt.decode(token, "mauvaise-cle", algorithms=[ALGORITHM])


def test_token_expire_est_rejete():
    payload = {
        "sub": "alice",
        "exp": datetime.utcnow() - timedelta(seconds=1),
    }
    token_expire = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    with pytest.raises(JWTError):
        jwt.decode(token_expire, SECRET_KEY, algorithms=[ALGORITHM])
