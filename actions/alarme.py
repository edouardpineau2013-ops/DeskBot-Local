from actions.temps import charger_alarmes, sauvegarder_alarmes
from datetime import datetime, timedelta

JOURS_SEMAINE = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]

SONNERIES_DISPONIBLES = {
    "alarme1": "sonneries/alarme 1.mp3",
    "alarme2": "sonneries/alarme 2.mp3",
    "alarme3": "sonneries/alarme 3.mp3",
    "alarme4": "sonneries/alarme 4.mp3",
}


def obtenir_alarme_principale():
    """Retourne l'alarme du site, ou None si aucune n'est configurée
    (ne crée plus de valeur par défaut automatiquement)."""

    data = charger_alarmes()

    if not data["alarmes"]:
        return None

    return data["alarmes"][0]


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
        data["alarmes"][0]["jours"] = jours if jours is not None else []
        data["alarmes"][0]["active"] = True

    sauvegarder_alarmes(data)

    return data["alarmes"][0]


def activer_desactiver_alarme():

    data = charger_alarmes()

    if not data["alarmes"]:
        return None

    data["alarmes"][0]["active"] = not data["alarmes"][0].get("active", False)
    sauvegarder_alarmes(data)

    return data["alarmes"][0]["active"]


def supprimer_alarme_principale():
    data = charger_alarmes()
    data["alarmes"] = []
    sauvegarder_alarmes(data)


def definir_sonnerie(chemin_fichier):

    data = charger_alarmes()

    if not data["alarmes"]:
        return False

    data["alarmes"][0]["sonnerie"] = chemin_fichier
    sauvegarder_alarmes(data)

    return True


def prochaine_alarme():

    data = charger_alarmes()

    if not data["alarmes"]:
        return None

    alarme = data["alarmes"][0]

    if not alarme.get("active", False):
        return None

    maintenant = datetime.now()
    jours = alarme.get("jours", [])
    heure = alarme.get("heure", 7)
    minute = alarme.get("minute", 0)

    for decalage in range(8):

        cible_jour = maintenant + timedelta(days=decalage)

        if jours and cible_jour.weekday() not in jours:
            continue

        cible = cible_jour.replace(hour=heure, minute=minute, second=0, microsecond=0)

        if cible <= maintenant:
            continue

        return cible - maintenant

    return None