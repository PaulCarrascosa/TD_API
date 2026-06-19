import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import generer_token, tokens_actifs
from datetime import datetime, timedelta


def test_generer_token_cree_une_entree():
    token = generer_token("alice")
    assert token in tokens_actifs


def test_token_associe_au_bon_utilisateur():
    token = generer_token("alice")
    assert tokens_actifs[token]["user"] == "alice"


def test_token_a_une_expiration_future():
    token = generer_token("alice")
    assert tokens_actifs[token]["expire_le"] > datetime.utcnow()


def test_deux_tokens_sont_differents():
    token1 = generer_token("alice")
    token2 = generer_token("alice")
    assert token1 != token2
