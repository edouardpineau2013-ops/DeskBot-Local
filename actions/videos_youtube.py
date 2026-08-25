# =========================================================
# VIDÉOS YOUTUBE - DESKBOT
# =========================================================

import os
import json
import requests
from pathlib import Path
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta


# =========================================================
# CONFIGURATION
# =========================================================

YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3"

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ABONNEMENTS_FILE = DATA_DIR / "youtube_abonnements.json"

DATA_DIR.mkdir(exist_ok=True)


# =========================================================
# API KEY
# =========================================================

def obtenir_cle_api():
    """
    Récupère la clé API YouTube depuis la variable
    d'environnement YOUTUBE_API_KEY.
    """

    cle = os.getenv("YOUTUBE_API_KEY")

    if not cle:
        print("❌ Variable YOUTUBE_API_KEY introuvable.")

    return cle


# =========================================================
# REQUÊTE API
# =========================================================

def requete_youtube(endpoint, params):
    """
    Effectue une requête vers l'API YouTube Data API v3.
    """

    cle = obtenir_cle_api()

    if not cle:
        return None

    params = dict(params)
    params["key"] = cle

    try:
        response = requests.get(
            f"{YOUTUBE_API_URL}/{endpoint}",
            params=params,
            timeout=15
        )

        if response.status_code != 200:
            print(
                "❌ Erreur YouTube API :",
                response.status_code,
                response.text
            )
            return None

        return response.json()

    except requests.RequestException as e:
        print(f"❌ Erreur réseau YouTube : {e}")
        return None


# =========================================================
# FORMATAGE VIDÉO
# =========================================================

def formater_video(video):
    """
    Transforme une vidéo YouTube en objet utilisable
    directement par le JavaScript.
    """

    snippet = video.get("snippet", {})
    video_id = video.get("id")

    if isinstance(video_id, dict):
        video_id = video_id.get("videoId")

    if not video_id:
        return None

    thumbnails = snippet.get("thumbnails", {})

    miniature = (
        thumbnails.get("maxres", {}).get("url")
        or thumbnails.get("high", {}).get("url")
        or thumbnails.get("medium", {}).get("url")
        or thumbnails.get("default", {}).get("url")
    )

    return {
        "id": video_id,
        "titre": snippet.get("title", "Sans titre"),
        "description": snippet.get("description", ""),
        "chaine": snippet.get("channelTitle", "Chaîne inconnue"),
        "channel_id": snippet.get("channelId"),
        "date": snippet.get("publishedAt"),
        "miniature": miniature,
        "url": f"https://www.youtube.com/watch?v={video_id}"
    }


# =========================================================
# RECHERCHE DE VIDÉOS
# =========================================================

def rechercher_videos(recherche, nombre=40):
    """
    Recherche des vidéos YouTube.
    """

    if not recherche or not recherche.strip():
        return []

    nombre = max(1, min(int(nombre), 50))

    data = requete_youtube(
        "search",
        {
            "part": "snippet",
            "q": recherche.strip(),
            "type": "video",
            "maxResults": nombre,
            "order": "relevance",
            "regionCode": "FR",
            "relevanceLanguage": "fr"
        }
    )

    if not data:
        return []

    videos = []

    for item in data.get("items", []):
        video = formater_video(item)

        if video:
            videos.append(video)

    return videos


# =========================================================
# VIDÉO PAR ID
# =========================================================

def obtenir_video(video_id):
    """
    Récupère les informations d'une vidéo précise.
    """

    if not video_id:
        return None

    data = requete_youtube(
        "videos",
        {
            "part": "snippet,contentDetails,statistics",
            "id": video_id
        }
    )

    if not data or not data.get("items"):
        return None

    video = formater_video(data["items"][0])

    if not video:
        return None

    item = data["items"][0]

    statistiques = item.get("statistics", {})
    contenu = item.get("contentDetails", {})

    video["vues"] = statistiques.get("viewCount", 0)
    video["likes"] = statistiques.get("likeCount", 0)
    video["duree"] = contenu.get("duration")

    return video


# =========================================================
# ABONNEMENTS
# =========================================================

def charger_abonnements():
    """
    Charge les abonnements depuis youtube_abonnements.json.
    """

    if not ABONNEMENTS_FILE.exists():
        return []

    try:
        with open(
            ABONNEMENTS_FILE,
            "r",
            encoding="utf-8"
        ) as fichier:
            donnees = json.load(fichier)

        if not isinstance(donnees, list):
            return []

        return donnees

    except (json.JSONDecodeError, OSError):
        return []


def sauvegarder_abonnements(abonnements):
    """
    Sauvegarde les abonnements.
    """

    try:
        with open(
            ABONNEMENTS_FILE,
            "w",
            encoding="utf-8"
        ) as fichier:
            json.dump(
                abonnements,
                fichier,
                ensure_ascii=False,
                indent=4
            )

        return True

    except OSError as e:
        print(f"❌ Impossible de sauvegarder les abonnements : {e}")
        return False


def ajouter_abonnement(channel_id, nom=None):
    """
    Ajoute une chaîne aux abonnements.
    """

    if not channel_id:
        return False

    abonnements = charger_abonnements()

    for abonnement in abonnements:
        if abonnement.get("channel_id") == channel_id:
            return True

    abonnements.append({
        "channel_id": channel_id,
        "nom": nom or "Chaîne inconnue"
    })

    return sauvegarder_abonnements(abonnements)


def supprimer_abonnement(channel_id):
    """
    Supprime une chaîne des abonnements.
    """

    abonnements = charger_abonnements()

    nouveaux = [
        abonnement
        for abonnement in abonnements
        if abonnement.get("channel_id") != channel_id
    ]

    if len(nouveaux) == len(abonnements):
        return False

    return sauvegarder_abonnements(nouveaux)


def est_abonne(channel_id):
    """
    Vérifie si une chaîne est actuellement suivie.
    """

    return any(
        abonnement.get("channel_id") == channel_id
        for abonnement in charger_abonnements()
    )


def obtenir_abonnements():
    """
    Retourne tous les abonnements.
    """

    return charger_abonnements()


# =========================================================
# VIDÉOS D'UNE CHAÎNE
# =========================================================

def obtenir_videos_chaine(channel_id, nombre=12):
    """
    Récupère les vidéos récentes d'une chaîne.
    """

    if not channel_id:
        return []

    nombre = max(1, min(int(nombre), 50))

    data = requete_youtube(
        "search",
        {
            "part": "snippet",
            "channelId": channel_id,
            "type": "video",
            "order": "date",
            "maxResults": nombre
        }
    )

    if not data:
        return []

    videos = []

    for item in data.get("items", []):
        video = formater_video(item)

        if video:
            videos.append(video)

    return videos

# =========================================================
# RSS YOUTUBE
# =========================================================

def obtenir_videos_rss(channel_id, nombre=15):

    if not channel_id:
        return []

    try:

        url = (
            "https://www.youtube.com/feeds/videos.xml"
            f"?channel_id={channel_id}"
        )

        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "DeskTube/1.0"
            }
        )

        if response.status_code != 200:
            print(
                f"❌ RSS YouTube {channel_id} : "
                f"HTTP {response.status_code}"
            )
            return []

        root = ET.fromstring(
            response.content
        )

        namespace = {
            "atom": "http://www.w3.org/2005/Atom",
            "yt": "http://www.youtube.com/xml/schemas/2015"
        }

        videos = []

        titre_chaine = ""

        titre_element = root.find(
            "atom:title",
            namespace
        )

        if titre_element is not None:
            titre_chaine = (
                titre_element.text or ""
            ).strip()

        for entry in root.findall(
            "atom:entry",
            namespace
        ):

            video_id_element = entry.find(
                "yt:videoId",
                namespace
            )

            titre_element = entry.find(
                "atom:title",
                namespace
            )

            date_element = entry.find(
                "atom:published",
                namespace
            )

            if video_id_element is None:
                continue

            video_id = (
                video_id_element.text or ""
            ).strip()

            if not video_id:
                continue

            titre = ""

            if titre_element is not None:
                titre = (
                    titre_element.text or ""
                ).strip()

            date = ""

            if date_element is not None:
                date = (
                    date_element.text or ""
                ).strip()

            videos.append({
                "id": video_id,
                "titre": titre,
                "chaine": titre_chaine,
                "miniature": (
                    f"https://i.ytimg.com/vi/"
                    f"{video_id}/hqdefault.jpg"
                ),
                "avatar": "",
                "date": date
            })

            if len(videos) >= nombre:
                break

        return videos

    except Exception as e:

        print(
            f"❌ Erreur RSS YouTube : {e}"
        )

        return []


# =========================================================
# VIDÉOS DES ABONNEMENTS
# =========================================================

def obtenir_videos_abonnements(
    nombre=50,
    seulement_trois_jours=False
):

    abonnements = charger_abonnements()

    videos = []

    ids_deja_vus = set()

    maintenant = datetime.now(
        timezone.utc
    )

    limite = maintenant - timedelta(
        days=3
    )

    for abonnement in abonnements:

        if not isinstance(
            abonnement,
            dict
        ):
            continue

        channel_id = abonnement.get(
            "channel_id"
        )

        if not channel_id:
            continue

        flux = obtenir_videos_rss(
            channel_id,
            nombre=15
        )

        for video in flux:

            video_id = video.get("id")

            if not video_id:
                continue

            if video_id in ids_deja_vus:
                continue

            # ---------------------------------------------
            # FILTRE 3 JOURS
            # ---------------------------------------------

            if seulement_trois_jours:

                date_video = video.get(
                    "date"
                )

                if not date_video:
                    continue

                try:

                    date_video = datetime.fromisoformat(
                        date_video.replace(
                            "Z",
                            "+00:00"
                        )
                    )

                    if date_video < limite:
                        continue

                except ValueError:

                    continue

            video["source"] = "abonnement"

            videos.append(video)

            ids_deja_vus.add(
                video_id
            )

    # Plus récent → plus ancien
    videos.sort(
        key=lambda video: video.get(
            "date",
            ""
        ),
        reverse=True
    )

    return videos[:nombre]


# =========================================================
# POUR TOI
# =========================================================

def obtenir_recommandations(nombre=40):

    """
    Mix de toutes les vidéos disponibles
    provenant des abonnements.
    """

    videos = obtenir_videos_abonnements(
        nombre=50,
        seulement_trois_jours=False
    )

    # Mélange pour éviter d'avoir
    # 15 vidéos de la même chaîne d'affilée.

    import random

    random.shuffle(videos)

    return videos[:nombre]


# =========================================================
# ABONNEMENTS
# =========================================================

def obtenir_dernieres_videos_abonnements(
    nombre=40
):

    """
    Dernières vidéos des abonnements
    publiées pendant les 3 derniers jours.
    """

    videos = obtenir_videos_abonnements(
        nombre=50,
        seulement_trois_jours=True
    )

    return videos[:nombre]


# =========================================================
# RECHERCHE DE CHAÎNES
# =========================================================

def rechercher_chaines(recherche, nombre=10):
    """
    Recherche des chaînes YouTube.
    """

    if not recherche or not recherche.strip():
        return []

    nombre = max(1, min(int(nombre), 50))

    data = requete_youtube(
        "search",
        {
            "part": "snippet",
            "q": recherche.strip(),
            "type": "channel",
            "maxResults": nombre,
            "regionCode": "FR",
            "relevanceLanguage": "fr"
        }
    )

    if not data:
        return []

    chaines = []

    for item in data.get("items", []):

        snippet = item.get("snippet", {})
        channel_id = item.get("id", {}).get("channelId")

        if not channel_id:
            continue

        thumbnails = snippet.get("thumbnails", {})

        avatar = (
            thumbnails.get("high", {}).get("url")
            or thumbnails.get("medium", {}).get("url")
            or thumbnails.get("default", {}).get("url")
        )

        chaines.append({
            "channel_id": channel_id,
            "nom": snippet.get(
                "title",
                "Chaîne inconnue"
            ),
            "description": snippet.get(
                "description",
                ""
            ),
            "avatar": avatar,
            "abonne": est_abonne(channel_id)
        })

    return chaines