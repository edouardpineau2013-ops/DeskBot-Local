import threading
import time
import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from audio.voix import parler, jouer_son
from actions.notifications import notifier_telephone


# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER_DATA = os.path.join(BASE_DIR, "data")
FICHIER_ALARMES = os.path.join(DOSSIER_DATA, "alarmes.json")

# Fuseau horaire de Paris
FUSEAU_PARIS = ZoneInfo("Europe/Paris")

gestionnaire_lance = False


# =========================================================
# HEURE ACTUELLE
# =========================================================

def maintenant_paris():
    """
    Retourne la date et l'heure actuelles
    dans le fuseau Europe/Paris.
    """
    return datetime.now(FUSEAU_PARIS)


# =========================================================
# ALARMES
# =========================================================

def verifier_alarmes(heure, minute):

    data = charger_alarmes()

    # Jour actuel en heure de Paris
    maintenant = maintenant_paris()
    aujourd_hui = maintenant.weekday()

    for alarme in data["alarmes"]:

        # Alarme désactivée
        if not alarme.get("active", False):
            continue

        # Vérification de l'heure
        if alarme.get("heure") != heure:
            continue

        if alarme.get("minute") != minute:
            continue

        # Vérification des jours
        jours = alarme.get("jours", [])

        if jours and aujourd_hui not in jours:
            continue

        # -------------------------------------------------
        # SONNERIE
        # -------------------------------------------------

        chemin_son = alarme.get(
            "sonnerie",
            "sonneries/alarme 1.mp3"
        )

        jouer_son(chemin_son)

        # -------------------------------------------------
        # VOIX DESKBOT
        # -------------------------------------------------

        message = "C'est l'heure de votre alarme !"

        parler(message)

        # -------------------------------------------------
        # NOTIFICATION TELEPHONE
        # -------------------------------------------------

        notifier_telephone(
            "DeskBot",
            message
        )

        print(
            f"🔔 Alarme déclenchée : "
            f"{heure:02d}:{minute:02d}"
        )


# =========================================================
# FICHIERS
# =========================================================

def creer_dossier():

    if not os.path.exists(DOSSIER_DATA):
        os.makedirs(DOSSIER_DATA)


def creer_fichier():

    creer_dossier()

    if not os.path.exists(FICHIER_ALARMES):

        with open(
            FICHIER_ALARMES,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                {
                    "alarmes": []
                },
                f,
                indent=4,
                ensure_ascii=False
            )


def charger_alarmes():

    creer_fichier()

    with open(
        FICHIER_ALARMES,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def sauvegarder_alarmes(data):

    creer_fichier()

    with open(
        FICHIER_ALARMES,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


# =========================================================
# BOUCLE DE SURVEILLANCE
# =========================================================

def boucle():

    derniere_minute = None

    while True:

        try:

            # Heure actuelle de Paris
            maintenant = maintenant_paris()

            cle = (
                maintenant.hour,
                maintenant.minute
            )

            # Vérification une seule fois par minute
            if cle != derniere_minute:

                derniere_minute = cle

                verifier_alarmes(
                    maintenant.hour,
                    maintenant.minute
                )

            time.sleep(1)

        except Exception as e:

            print(
                "❌ Erreur gestionnaire Temps :",
                e
            )

            time.sleep(1)


# =========================================================
# LANCEMENT
# =========================================================

def lancer_gestionnaire():

    global gestionnaire_lance

    if gestionnaire_lance:
        return

    creer_fichier()

    thread = threading.Thread(
        target=boucle,
        daemon=True
    )

    thread.start()

    gestionnaire_lance = True

    print(
        "⏰ Gestionnaire Temps lancé "
        "avec le fuseau Europe/Paris."
    )