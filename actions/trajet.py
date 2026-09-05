import requests
import os


CLE_API_ORS = os.environ.get("ORS_API_KEY", "")


PROFILS = {
    "voiture": "driving-car",
    "en voiture": "driving-car",

    "vélo": "cycling-regular",
    "velo": "cycling-regular",
    "en vélo": "cycling-regular",
    "en velo": "cycling-regular",

    "pied": "foot-walking",
    "à pied": "foot-walking",
    "a pied": "foot-walking",
}


def _geocoder(adresse):
    """Convertit un nom de lieu en (longitude, latitude)."""

    url = "https://api.openrouteservice.org/geocode/search"

    params = {
        "api_key": CLE_API_ORS,
        "text": adresse,
        "size": 1
    }

    try:
        reponse = requests.get(
            url,
            params=params,
            timeout=10
        )
    except Exception as e:
        print("Erreur géocodage :", e)
        return None

    if reponse.status_code != 200:
        print(
            "Erreur géocodage :",
            reponse.status_code,
            reponse.text[:300]
        )
        return None

    try:
        features = reponse.json().get("features", [])
    except Exception as e:
        print("Erreur JSON géocodage :", e)
        return None

    if not features:
        print("Aucun résultat pour :", adresse)
        return None

    try:
        return tuple(
            features[0]["geometry"]["coordinates"]
        )
    except (KeyError, TypeError, IndexError):
        print("Coordonnées introuvables pour :", adresse)
        return None


def _normaliser_mode(mode):
    """Normalise le moyen de transport."""

    if mode is None:
        return None

    mode = mode.strip().lower()

    modes = {
        "voiture": "voiture",
        "en voiture": "voiture",
        "à voiture": "voiture",
        "a voiture": "voiture",

        "vélo": "velo",
        "velo": "velo",
        "en vélo": "velo",
        "en velo": "velo",
        "à vélo": "velo",
        "a velo": "velo",

        "pied": "pied",
        "à pied": "pied",
        "a pied": "pied",
        "à pieds": "pied",
        "a pieds": "pied",
        "en marchant": "pied",
    }

    return modes.get(mode)


def calculer_trajet(depart, arrivee, mode):
    """Retourne (distance_km, duree_minutes) ou None."""

    # =====================================================
    # NORMALISATION DU MODE
    # =====================================================

    mode = _normaliser_mode(mode)

    print("MODE REÇU :", repr(mode))

    if mode is None:
        print("Mode de transport inconnu.")
        return None

    # =====================================================
    # PROFIL
    # =====================================================

    profil = PROFILS.get(mode)

    print("PROFIL ORS :", profil)

    if profil is None:
        return None

    # =====================================================
    # GÉOCODAGE
    # =====================================================

    coord_depart = _geocoder(depart)
    coord_arrivee = _geocoder(arrivee)

    if coord_depart is None:
        print("Départ introuvable :", depart)
        return None

    if coord_arrivee is None:
        print("Arrivée introuvable :", arrivee)
        return None

    print("COORDONNÉES DÉPART :", coord_depart)
    print("COORDONNÉES ARRIVÉE :", coord_arrivee)

    # =====================================================
    # DIRECTIONS
    # =====================================================

    url = f"https://api.heigit.org/v2/directions/{profil}"

    headers = {
        "Authorization": CLE_API_ORS,
        "Content-Type": "application/json"
    }

    payload = {
        "coordinates": [
            list(coord_depart),
            list(coord_arrivee)
        ]
    }

    try:
        reponse = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=20
        )
    except Exception as e:
        print("Erreur trajet :", e)
        return None

    if reponse.status_code != 200:
        print(
            "Erreur trajet :",
            reponse.status_code,
            reponse.text[:500]
        )
        return None

    # =====================================================
    # RÉPONSE
    # =====================================================

    try:
        donnees = reponse.json()

        resume = (
            donnees["features"][0]
            ["properties"]
            ["summary"]
        )

        distance_km = resume["distance"] / 1000
        duree_minutes = resume["duration"] / 60

    except (KeyError, IndexError, TypeError, ValueError) as e:
        print("Erreur lecture trajet :", e)
        print("Réponse API :", reponse.text[:500])
        return None

    return distance_km, duree_minutes