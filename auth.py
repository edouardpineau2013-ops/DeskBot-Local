import hashlib
import hmac
import secrets
import json
import os

FICHIER_TOKENS = "tokens.json"

# Remplace par ton vrai mot de passe UNE FOIS, note le hash affiché
# dans la console au premier lancement, puis tu peux remettre autre
# chose ici si tu veux — seul MOT_DE_PASSE_HASH compte pour la verif.
MOT_DE_PASSE = os.environ.get("DESKBOT_PASSWORD", "change-moi")
MOT_DE_PASSE_HASH = hashlib.sha256(MOT_DE_PASSE.encode()).hexdigest()


def _charger_tokens():
    if not os.path.exists(FICHIER_TOKENS):
        return set()
    with open(FICHIER_TOKENS, "r") as f:
        return set(json.load(f))


def _sauvegarder_tokens(tokens):
    with open(FICHIER_TOKENS, "w") as f:
        json.dump(list(tokens), f)


def verifier_mot_de_passe(mot_de_passe_saisi):
    hash_saisi = hashlib.sha256(mot_de_passe_saisi.encode()).hexdigest()
    return hmac.compare_digest(hash_saisi, MOT_DE_PASSE_HASH)


def generer_token():
    token = secrets.token_hex(32)
    tokens = _charger_tokens()
    tokens.add(token)
    _sauvegarder_tokens(tokens)
    return token


def token_valide(token):
    return token in _charger_tokens()