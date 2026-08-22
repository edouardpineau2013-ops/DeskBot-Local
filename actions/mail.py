import os
import json
import threading
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from audio.voix import parler, notifier_telephone

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

FICHIER_VUS = "data/mails_vus.json"

gestionnaire_mails_lance = False


def _obtenir_service():
    creds = None

    # Récupération de la connexion déjà enregistrée
    if os.path.exists("token_mail.json"):
        creds = Credentials.from_authorized_user_file(
            "token_mail.json",
            SCOPES
        )

    # Connexion encore valide
    if creds and creds.valid:
        return build("gmail", "v1", credentials=creds)

    # Le token d'accès a expiré, mais le refresh token permet
    # de le renouveler automatiquement.
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())

            with open("token_mail.json", "w", encoding="utf-8") as f:
                f.write(creds.to_json())

            return build("gmail", "v1", credentials=creds)

        except Exception as e:
            print("⚠️ Impossible de renouveler le token Gmail :", e)
            print("⚠️ Le refresh token est invalide. Autorisation Gmail nécessaire.")
            return None

    # Première connexion OU ancienne connexion révoquée
    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials_mail.json",
        SCOPES
    )

    creds = flow.run_local_server(port=0)

    # On sauvegarde le refresh token
    with open("token_mail.json", "w", encoding="utf-8") as f:
        f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def _charger_vus():
    if not os.path.exists(FICHIER_VUS):
        return set()
    with open(FICHIER_VUS, "r") as f:
        return set(json.load(f))


def _sauvegarder_vus(vus):
    os.makedirs("data", exist_ok=True)
    with open(FICHIER_VUS, "w") as f:
        json.dump(list(vus), f)


def _extraire_expediteur_sujet(service, message_id):

    message = service.users().messages().get(
        userId="me", id=message_id, format="metadata",
        metadataHeaders=["From", "Subject"]
    ).execute()

    headers = {h["name"]: h["value"] for h in message["payload"]["headers"]}
    expediteur = headers.get("From", "expéditeur inconnu")
    sujet = headers.get("Subject", "(sans objet)")

    if "<" in expediteur:
        expediteur = expediteur.split("<")[0].strip().strip('"')

    return expediteur, sujet


def etat_mails_non_lus(max_details=100):
    """Retourne (nombre_total, [(expediteur, sujet), ...]) hors promotions."""

    service = _obtenir_service()

    resultat = service.users().messages().list(
        userId="me", q="in:inbox is:unread -category:promotions", maxResults=100
    ).execute()

    messages = resultat.get("messages", [])
    total = len(messages)

    details = []
    for message in messages[:max_details]:
        expediteur, sujet = _extraire_expediteur_sujet(service, message["id"])
        details.append((expediteur, sujet))

    return total, details


def verifier_nouveaux_mails():
    """Retourne les (expediteur, sujet) des mails non lus jamais vus avant."""

    service = _obtenir_service()

    resultat = service.users().messages().list(
        userId="me", q="in:inbox is:unread -category:promotions", maxResults=20
    ).execute()

    messages = resultat.get("messages", [])
    vus = _charger_vus()
    nouveaux = []

    for message in messages:
        if message["id"] not in vus:
            expediteur, sujet = _extraire_expediteur_sujet(service, message["id"])
            nouveaux.append((expediteur, sujet))
            vus.add(message["id"])

    if nouveaux:
        _sauvegarder_vus(vus)

    return nouveaux


def _boucle_mails(intervalle_secondes=180):
    while True:
        try:
            nouveaux = verifier_nouveaux_mails()
            for expediteur, sujet in nouveaux:
                message = f"Nouveau mail de {expediteur} : {sujet}"
                parler(message)
                notifier_telephone("📧 DeskBot", message)
        except Exception as e:
            print("Erreur vérification mails :", e)

        time.sleep(intervalle_secondes)


def lancer_gestionnaire_mails():
    global gestionnaire_mails_lance
    if gestionnaire_mails_lance:
        return
    thread = threading.Thread(target=_boucle_mails, daemon=True)
    thread.start()
    gestionnaire_mails_lance = True
    print("📧 Gestionnaire Mails lancé.")