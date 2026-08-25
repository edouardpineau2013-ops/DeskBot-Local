from actions.temps import charger_alarmes, sauvegarder_alarmes
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# =========================================================
# CONFIGURATION
# =========================================================

FUSEAU_PARIS = ZoneInfo("Europe/Paris")

JOURS_SEMAINE = [
    "lundi",
    "mardi",
    "mercredi",
    "jeudi",
    "vendredi",
    "samedi",
    "dimanche"
]

SONNERIES_DISPONIBLES = {
    "alarme1": "sonneries/alarme 1.mp3",
    "alarme2": "sonneries/alarme 2.mp3",
    "alarme3": "sonneries/alarme 3.mp3",
    "alarme4": "sonneries/alarme 4.mp3",
}


# =========================================================
# ALARME PRINCIPALE
# =========================================================

def obtenir_alarme_principale():
    """
    Retourne l'alarme du site,
    ou None si aucune n'est configurée.
    """

    data = charger_alarmes()

    if not data["alarmes"]:
        return None

    return data["alarmes"][0]


# =========================================================
# DEFINIR UNE ALARME
# =========================================================

def definir_alarme(heures, minutes, jours=None):

    data = charger_alarmes()

    if not data["alarmes"]:

        data["alarmes"].append({
            "heure": heures,
            "minute": minutes,
            "active": True,
            "jours": jours or [],
            "sonnerie": "sonneries/alarme 1.mp3"
        })

    else:

        data["alarmes"][0]["heure"] = heures
        data["alarmes"][0]["minute"] = minutes

        data["alarmes"][0]["jours"] = (
            jours
            if jours is not None
            else []
        )

        data["alarmes"][0]["active"] = True

    sauvegarder_alarmes(data)

    return data["alarmes"][0]


# =========================================================
# ACTIVER / DESACTIVER
# =========================================================

def activer_desactiver_alarme():

    data = charger_alarmes()

    if not data["alarmes"]:
        return None

    data["alarmes"][0]["active"] = not data["alarmes"][0].get(
        "active",
        False
    )

    sauvegarder_alarmes(data)

    return data["alarmes"][0]["active"]


# =========================================================
# SUPPRIMER
# =========================================================

def supprimer_alarme_principale():

    data = charger_alarmes()

    data["alarmes"] = []

    sauvegarder_alarmes(data)


# =========================================================
# SONNERIE
# =========================================================

def definir_sonnerie(chemin_fichier):

    data = charger_alarmes()

    if not data["alarmes"]:
        return False

    data["alarmes"][0]["sonnerie"] = chemin_fichier

    sauvegarder_alarmes(data)

    return True


# =========================================================
# PROCHAINE ALARME
# =========================================================

def prochaine_alarme():

    data = charger_alarmes()

    if not data["alarmes"]:
        return None

    alarme = data["alarmes"][0]

    if not alarme.get("active", False):
        return None

    # Heure actuelle de Paris
    maintenant = datetime.now(FUSEAU_PARIS)

    jours = alarme.get("jours", [])

    heure = alarme.get(
        "heure",
        7
    )

    minute = alarme.get(
        "minute",
        0
    )

    # Recherche sur les 7 prochains jours
    for decalage in range(8):

        cible_jour = maintenant + timedelta(
            days=decalage
        )

        # Si des jours spécifiques sont définis
        if (
            jours
            and cible_jour.weekday() not in jours
        ):
            continue

        cible = cible_jour.replace(
            hour=heure,
            minute=minute,
            second=0,
            microsecond=0
        )

        # L'alarme doit être dans le futur
        if cible <= maintenant:
            continue

        return cible - maintenant

    return None