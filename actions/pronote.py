import pronotepy
from pronotepy.ent import cas_seinesaintdenis_edu
from datetime import date, timedelta
import os

URL_PRONOTE = os.environ.get("PRONOTE_URL", "")
IDENTIFIANT = os.environ.get("PRONOTE_IDENTIFIANT", "")
MOT_DE_PASSE = os.environ.get("PRONOTE_MOT_DE_PASSE", "")


def _connexion():
    try:
        client = pronotepy.Client(
            URL_PRONOTE,
            username=IDENTIFIANT,
            password=MOT_DE_PASSE,
            ent=cas_seinesaintdenis_edu
        )
        if not client.logged_in:
            return None
        return client
    except Exception as e:
        print("Erreur connexion Pronote :", e)
        return None


def obtenir_emploi_du_temps(jour_offset=0):
    """Retourne la liste des cours du jour demande (0 = aujourd'hui)."""

    client = _connexion()
    if client is None:
        return None

    jour_cible = date.today() + timedelta(days=jour_offset)
    cours = client.lessons(jour_cible)

    resultat = []
    for c in cours:
        resultat.append({
            "matiere": c.subject.name if c.subject else "Matière inconnue",
            "debut": c.start.strftime("%Hh%M"),
            "fin": c.end.strftime("%Hh%M"),
            "annule": c.canceled
        })

    return resultat


def obtenir_devoirs(jours_a_venir=7):
    """Retourne les devoirs des N prochains jours."""

    client = _connexion()
    if client is None:
        return None

    aujourdhui = date.today()
    devoirs = client.homework(aujourdhui, aujourdhui + timedelta(days=jours_a_venir))

    resultat = []
    for d in devoirs:
        resultat.append({
            "matiere": d.subject.name if d.subject else "Matière inconnue",
            "date": d.date.strftime("%d/%m"),
            "description": d.description
        })

    return resultat


def obtenir_moyenne_generale():
    """Retourne la moyenne generale de la periode en cours, ou None."""

    client = _connexion()
    if client is None:
        return None

    if not client.periods:
        return None

    periode_actuelle = client.periods[-1]  # la plus recente

    try:
        return periode_actuelle.overall_average
    except AttributeError:
        return None


def obtenir_profs_absents(jour_offset=0):
    """Retourne la liste des cours annules (prof absent) du jour demande."""

    cours = obtenir_emploi_du_temps(jour_offset)

    if cours is None:
        return None

    return [c for c in cours if c["annule"]]