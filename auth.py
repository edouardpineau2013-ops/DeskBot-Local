import os
import secrets
import hashlib
import hmac
import base64
import json
import time


# ============================================================
# CONFIGURATION
# ============================================================

MOT_DE_PASSE = os.environ.get(
    "DESKBOT_PASSWORD",
    "change-moi"
)

# Secret utilisé pour signer les tokens.
#
# Sur Render :
# DESKBOT_AUTH_SECRET doit être défini dans
# Environment Variables.
#
# En local :
# si la variable n'existe pas, un secret local est utilisé.
#
# IMPORTANT :
# sur Render, cette variable doit rester la même.
SECRET_AUTH = os.environ.get(
    "DESKBOT_AUTH_SECRET"
)

if not SECRET_AUTH:
    # Secret de secours pour le développement local.
    #
    # Il est volontairement fixe afin que les tokens
    # restent valides pendant que le serveur tourne.
    SECRET_AUTH = "deskbot-local-secret-change-moi"


SECRET_AUTH = SECRET_AUTH.encode("utf-8")


# Durée de validité du token
#
# 30 jours = 30 * 24 * 60 * 60
DUREE_TOKEN = 30 * 24 * 60 * 60


# ============================================================
# HASH DU MOT DE PASSE
# ============================================================

MOT_DE_PASSE_HASH = hashlib.sha256(
    MOT_DE_PASSE.encode("utf-8")
).hexdigest()


# ============================================================
# UTILITAIRES BASE64
# ============================================================

def _base64_encode(texte):
    return base64.urlsafe_b64encode(
        texte
    ).decode("utf-8").rstrip("=")


def _base64_decode(texte):
    padding = "=" * (
        4 - len(texte) % 4
    )

    return base64.urlsafe_b64decode(
        texte + padding
    )


# ============================================================
# SIGNATURE DU TOKEN
# ============================================================

def _signer(message):
    signature = hmac.new(
        SECRET_AUTH,
        message.encode("utf-8"),
        hashlib.sha256
    ).digest()

    return _base64_encode(signature)


# ============================================================
# VÉRIFIER LE MOT DE PASSE
# ============================================================

def verifier_mot_de_passe(mot_de_passe):

    if not isinstance(
        mot_de_passe,
        str
    ):
        return False

    hash_fourni = hashlib.sha256(
        mot_de_passe.encode("utf-8")
    ).hexdigest()

    return hmac.compare_digest(
        hash_fourni,
        MOT_DE_PASSE_HASH
    )


# ============================================================
# GÉNÉRER UN TOKEN
# ============================================================

def generer_token():

    maintenant = int(
        time.time()
    )

    expiration = (
        maintenant
        + DUREE_TOKEN
    )

    identifiant = secrets.token_urlsafe(
        32
    )

    donnees = {
        "id": identifiant,
        "iat": maintenant,
        "exp": expiration
    }

    payload = _base64_encode(
        json.dumps(
            donnees,
            separators=(",", ":")
        ).encode("utf-8")
    )

    signature = _signer(
        payload
    )

    token = (
        payload
        + "."
        + signature
    )

    return token


# ============================================================
# VÉRIFIER UN TOKEN
# ============================================================

def token_valide(token):

    if not token:
        return False

    if not isinstance(
        token,
        str
    ):
        return False

    try:

        # Le token doit avoir exactement :
        #
        # payload.signature
        #
        morceaux = token.split(".")

        if len(morceaux) != 2:
            return False

        payload = morceaux[0]
        signature = morceaux[1]

        # ----------------------------------------------------
        # Vérification de la signature
        # ----------------------------------------------------

        signature_attendue = _signer(
            payload
        )

        if not hmac.compare_digest(
            signature,
            signature_attendue
        ):
            print("❌ Signature token invalide")
            return False

        # ----------------------------------------------------
        # Décodage du payload
        # ----------------------------------------------------

        donnees = json.loads(
            _base64_decode(
                payload
            ).decode("utf-8")
        )

        # ----------------------------------------------------
        # Vérification de l'expiration
        # ----------------------------------------------------

        expiration = donnees.get(
            "exp"
        )

        if not expiration:
            return False

        if int(time.time()) >= int(
            expiration
        ):
            return False

        # ----------------------------------------------------
        # Vérification de l'identifiant
        # ----------------------------------------------------

        if not donnees.get("id"):
            return False

        return True

    except Exception as e:

        print(
            f"⚠️ Token invalide : {e}"
        )

        return False