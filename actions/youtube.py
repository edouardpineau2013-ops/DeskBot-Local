import requests

CLE_API_YOUTUBE = "AIzaSyAs2rZLXgwZRZLVYAKYkMaXUKwSGicZ1II"


def obtenir_stats_chaine(identifiant, par_handle=True):
    """
    identifiant : un handle YouTube (ex: '@MaChaine') ou un ID de chaîne.
    Retourne {nom, abonnes, vues, videos} ou None si la chaîne n'existe pas.
    """

    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "snippet,statistics",
        "key": CLE_API_YOUTUBE,
    }

    if par_handle:
        params["forHandle"] = identifiant
    else:
        params["id"] = identifiant

    try:
        reponse = requests.get(url, params=params, timeout=10)
    except Exception as e:
        print("Erreur YouTube :", e)
        return None

    if reponse.status_code != 200:
        print("Erreur YouTube :", reponse.status_code, reponse.text[:300])
        return None

    items = reponse.json().get("items", [])

    if not items:
        return None

    chaine = items[0]
    stats = chaine["statistics"]

    abonnes_caches = stats.get("hiddenSubscriberCount", False)
    abonnes = None if abonnes_caches else int(stats.get("subscriberCount", 0))

    return {
        "nom": chaine["snippet"]["title"],
        "abonnes": abonnes,
        "vues": int(stats.get("viewCount", 0)),
        "videos": int(stats.get("videoCount", 0)),
    }