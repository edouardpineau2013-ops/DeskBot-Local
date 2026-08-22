import os
import requests

CLE_API_ORS = os.environ.get("ORS_API_KEY", "")

PROFILS = {
    "voiture": "driving-car",
    "velo": "cycling-regular",
    "pied": "foot-walking",
}


def _geocoder(adresse):
    """Convertit un nom de lieu en (longitude, latitude)."""

    url = "https://api.openrouteservice.org/geocode/search"
    params = {"api_key": CLE_API_ORS, "text": adresse, "size": 1}

    try:
        reponse = requests.get(url, params=params, timeout=10)
    except Exception as e:
        print("Erreur géocodage :", e)
        return None

    if reponse.status_code != 200:
        return None

    features = reponse.json().get("features", [])

    if not features:
        return None

    return tuple(features[0]["geometry"]["coordinates"])  # (lon, lat)


def calculer_trajet(depart, arrivee, mode="voiture"):
    """Retourne (distance_km, duree_minutes) ou None si echec."""

    coord_depart = _geocoder(depart)
    coord_arrivee = _geocoder(arrivee)

    if coord_depart is None or coord_arrivee is None:
        return None

    profil = PROFILS.get(mode, "driving-car")

    url = f"https://api.openrouteservice.org/v2/directions/{profil}"
    params = {
        "api_key": CLE_API_ORS,
        "start": f"{coord_depart[0]},{coord_depart[1]}",
        "end": f"{coord_arrivee[0]},{coord_arrivee[1]}",
    }

    try:
        reponse = requests.get(url, params=params, timeout=10)
    except Exception as e:
        print("Erreur trajet :", e)
        return None

    if reponse.status_code != 200:
        print("Erreur trajet :", reponse.status_code, reponse.text[:300])
        return None

    donnees = reponse.json()

    try:
        resume = donnees["features"][0]["properties"]["summary"]
    except (KeyError, IndexError):
        return None

    return resume["distance"] / 1000, resume["duration"] / 60