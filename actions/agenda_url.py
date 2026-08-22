import json
import requests
import re

from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

from actions.agenda import ajouter_evenement


FUSEAU = ZoneInfo("Europe/Paris")


def recuperer_page(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/151.0 Safari/537.36"
        )
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=15
    )

    response.raise_for_status()

    return response.text


def extraire_evenement_jsonld(html):
    soup = BeautifulSoup(html, "html.parser")

    scripts = soup.find_all(
        "script",
        type="application/ld+json"
    )

    evenements = []

    for script in scripts:

        try:
            donnees = json.loads(
                script.string or script.get_text()
            )
        except Exception:
            continue

        if isinstance(donnees, dict):

            if donnees.get("@type") == "Event":
                evenements.append(donnees)

            elif isinstance(donnees.get("@graph"), list):

                for element in donnees["@graph"]:

                    if (
                        isinstance(element, dict)
                        and element.get("@type") == "Event"
                    ):
                        evenements.append(element)

        elif isinstance(donnees, list):

            for element in donnees:

                if (
                    isinstance(element, dict)
                    and element.get("@type") == "Event"
                ):
                    evenements.append(element)

    if not evenements:
        return None

    return evenements[0]


def convertir_date(date_texte):

    if not date_texte:
        return None

    date_texte = date_texte.strip()

    try:
        date = datetime.fromisoformat(
            date_texte.replace("Z", "+00:00")
        )

    except ValueError:

        try:
            date = datetime.strptime(
                date_texte,
                "%Y-%m-%d"
            )

        except ValueError:
            return None

    if date.tzinfo is None:
        date = date.replace(
            tzinfo=FUSEAU
        )

    return date.astimezone(FUSEAU)

def extraire_heure_depuis_html(html):
    """
    Cherche une heure dans le contenu visible de la page.

    Formats acceptés :
        19h00
        19 h 00
        19:00
        19 heures
    """

    soup = BeautifulSoup(html, "html.parser")

    # On récupère uniquement le texte visible
    texte = soup.get_text(" ", strip=True)

    motifs = [
        # 19h00 / 19 h 00
        r"\b([01]?\d|2[0-3])\s*h\s*(\d{2})\b",

        # 19:00
        r"\b([01]?\d|2[0-3]):([0-5]\d)\b",

        # 19 heures / 19 heure
        r"\b([01]?\d|2[0-3])\s+heures?\b"
    ]

    for motif in motifs:

        resultat = re.search(
            motif,
            texte,
            re.IGNORECASE
        )

        if not resultat:
            continue

        heures = int(resultat.group(1))

        if len(resultat.groups()) >= 2 and resultat.group(2):
            minutes = int(resultat.group(2))
        else:
            minutes = 0

        return f"{heures:02d}:{minutes:02d}"

    return None


def extraire_lieu(evenement):

    lieu = evenement.get("location")

    if not lieu:
        return None

    if isinstance(lieu, str):
        return lieu

    nom = lieu.get("name")

    adresse = lieu.get("address")

    if isinstance(adresse, dict):

        morceaux = []

        for cle in [
            "streetAddress",
            "postalCode",
            "addressLocality"
        ]:

            valeur = adresse.get(cle)

            if valeur:
                morceaux.append(str(valeur))

        adresse = ", ".join(morceaux)

    if nom and adresse:
        return f"{nom}, {adresse}"

    return nom or adresse


def analyser_evenement(url):

    html = recuperer_page(url)

    evenement = extraire_evenement_jsonld(html)

    if not evenement:
        raise ValueError(
            "Aucun événement structuré trouvé sur cette page."
        )

    titre = evenement.get(
        "name",
        "Événement"
    )

    # =====================================================
    # DATE / HEURE DE DÉBUT
    # =====================================================

    start_date = evenement.get("startDate")

    debut = convertir_date(start_date)

    # -----------------------------------------------------
    # Si le JSON-LD ne contient pas l'heure, on cherche
    # l'heure directement dans la page.
    # -----------------------------------------------------

    heure_html = extraire_heure_depuis_html(html)

    if debut and heure_html:

        heures, minutes = map(
            int,
            heure_html.split(":")
        )

        debut = debut.replace(
            hour=heures,
            minute=minutes,
            second=0,
            microsecond=0
        )

    # -----------------------------------------------------
    # Impossible de déterminer la date
    # -----------------------------------------------------

    if not debut:
        raise ValueError(
            "La date de début de l'événement est introuvable."
        )

    # =====================================================
    # DATE / HEURE DE FIN
    # =====================================================

    fin = convertir_date(
        evenement.get("endDate")
    )

    # Si la fin existe mais n'a pas d'heure alors que le
    # début en a une, on pourra utiliser une durée par défaut.
    if fin and fin <= debut:
        fin = None

    # =====================================================
    # DURÉE
    # =====================================================

    if fin:

        duree_minutes = int(
            (fin - debut).total_seconds() / 60
        )

        if duree_minutes <= 0:
            duree_minutes = 60

    else:
        duree_minutes = 60

    # =====================================================
    # DESCRIPTION
    # =====================================================

    description = evenement.get(
        "description"
    )

    # =====================================================
    # LIEU
    # =====================================================

    lieu = extraire_lieu(
        evenement
    )

    return {
        "titre": titre,
        "date": debut.strftime("%Y-%m-%d"),
        "heure_debut": debut.strftime("%H:%M"),
        "duree_minutes": duree_minutes,
        "description": description,
        "lieu": lieu
    }


def ajouter_evenement_depuis_url(url):

    donnees = analyser_evenement(url)

    evenement = ajouter_evenement(
        titre=donnees["titre"],
        date=donnees["date"],
        heure_debut=donnees["heure_debut"],
        duree_minutes=donnees["duree_minutes"],
        description=donnees["description"],
        lieu=donnees["lieu"]
    )

    date_affichage = datetime.strptime(
        donnees["date"],
        "%Y-%m-%d"
    ).strftime("%d/%m/%Y")

    heures, minutes = map(
        int,
        donnees["heure_debut"].split(":")
    )

    if minutes:
        heure_affichage = (
            f"{heures} heures {minutes} minutes"
        )
    else:
        heure_affichage = (
            f"{heures} heures"
        )

    return {
        "evenement": evenement,
        "message": (
            f"J'ai ajouté « {donnees['titre']} » "
            f"à ton agenda le {date_affichage} "
            f"à {heure_affichage}."
        )
    }