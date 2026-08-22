import threading
import time
import os
import json
from datetime import datetime
from audio.voix import parler, jouer_son, notifier_telephone

DOSSIER_DATA = "data"
FICHIER_ALARMES = os.path.join(DOSSIER_DATA, "alarmes.json")

gestionnaire_lance = False

def verifier_alarmes(heure, minute):

    data = charger_alarmes()
    aujourd_hui = datetime.now().weekday()

    for alarme in data["alarmes"]:

        if not alarme.get("active", False):
            continue

        if alarme.get("heure") != heure or alarme.get("minute") != minute:
            continue

        jours = alarme.get("jours", [])
        if jours and aujourd_hui not in jours:
            continue

        chemin_son = alarme.get("sonnerie", "sonneries/alarme 1.mp3")
        jouer_son(chemin_son)
        parler("C'est l'heure de votre alarme !")
        notifier_telephone("🔔 DeskBot", "C'est l'heure de votre alarme !")

def creer_dossier():

    if not os.path.exists(DOSSIER_DATA):
        os.makedirs(DOSSIER_DATA)


def creer_fichier():

    creer_dossier()

    if not os.path.exists(FICHIER_ALARMES):

        with open(FICHIER_ALARMES, "w", encoding="utf-8") as f:

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

    with open(FICHIER_ALARMES, "r", encoding="utf-8") as f:

        return json.load(f)


def sauvegarder_alarmes(data):

    with open(FICHIER_ALARMES, "w", encoding="utf-8") as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


def boucle():

    derniere_minute = None

    while True:

        time.sleep(1)

        maintenant = datetime.now()
        cle = (maintenant.hour, maintenant.minute)

        if cle != derniere_minute:
            derniere_minute = cle
            verifier_alarmes(maintenant.hour, maintenant.minute)

    while True:

        time.sleep(1)


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

    print("⏰ Gestionnaire Temps lancé.")