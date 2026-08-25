import os
import uuid
from pathlib import Path
from urllib.parse import quote

import requests


# =========================================================
# CONFIGURATION
# =========================================================

MODELE_IMAGE = "flux"

DOSSIER_IMAGES = Path("data/images_temp")
DOSSIER_IMAGES.mkdir(parents=True, exist_ok=True)

FORMATS_IMAGE = {
    "1:1": (1, 1),
    "16:9": (16, 9),
    "9:16": (9, 16),
    "4:3": (4, 3),
    "3:4": (3, 4),
    "3:2": (3, 2),
    "2:3": (2, 3),
}

QUALITES_IMAGE = {
    "basse": 768,
    "moyenne": 1024,
    "haute": 1280,
    "ultra": 1536,
}

#CALCULER LES DIMENSIONS

def calculer_dimensions(format_image="1:1", qualite="moyenne"):
    if format_image not in FORMATS_IMAGE:
        raise ValueError(
            f"Format invalide : {format_image}"
        )

    if qualite not in QUALITES_IMAGE:
        raise ValueError(
            f"Qualité invalide : {qualite}"
        )

    ratio_largeur, ratio_hauteur = FORMATS_IMAGE[format_image]
    taille = QUALITES_IMAGE[qualite]

    if ratio_largeur >= ratio_hauteur:
        largeur = taille
        hauteur = round(taille * ratio_hauteur / ratio_largeur)
    else:
        hauteur = taille
        largeur = round(taille * ratio_largeur / ratio_hauteur)

    return largeur, hauteur


# =========================================================
# GÉNÉRER UNE IMAGE
# =========================================================

def generer_image(prompt, format_image="1:1", qualite="moyenne"):
    """
    Génère une image avec Pollinations.
    Retourne le chemin du fichier généré.
    """

    if not prompt or not prompt.strip():
        raise ValueError("Le prompt ne peut pas être vide.")

    api_key = os.getenv("POLLINATIONS_API_KEY")

    if not api_key:
        raise RuntimeError(
            "La variable POLLINATIONS_API_KEY est introuvable."
        )

    largeur, hauteur = calculer_dimensions(
        format_image,
        qualite
    )

    prompt = prompt.strip()
    prompt_encode = quote(prompt)

    url = (
        f"https://gen.pollinations.ai/image/"
        f"{prompt_encode}"
        f"?model={MODELE_IMAGE}"
        f"&width={largeur}"
        f"&height={hauteur}"
    )

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        reponse = requests.get(
            url,
            headers=headers,
            timeout=180
        )
    except requests.RequestException as e:
        raise RuntimeError(
            f"Impossible de contacter Pollinations : {e}"
        ) from e

    if reponse.status_code != 200:
        raise RuntimeError(
            f"Pollinations a retourné HTTP "
            f"{reponse.status_code} : "
            f"{reponse.text[:500]}"
        )

    if not reponse.content:
        raise RuntimeError(
            "Pollinations a retourné une image vide."
        )

    nom_fichier = f"image_{uuid.uuid4().hex}.jpg"
    chemin = DOSSIER_IMAGES / nom_fichier

    try:
        with open(chemin, "wb") as fichier:
            fichier.write(reponse.content)
    except OSError as e:
        raise RuntimeError(
            f"Impossible d'enregistrer l'image : {e}"
        ) from e

    return str(chemin)


# =========================================================
# SUPPRIMER UNE IMAGE
# =========================================================

def supprimer_image(chemin):
    """
    Supprime une image générée.
    """

    if not chemin:
        return False

    try:
        fichier = Path(chemin)

        if fichier.exists():
            fichier.unlink()
            return True

    except OSError:
        pass

    return False


# =========================================================
# NETTOYER LES IMAGES TEMPORAIRES
# =========================================================

def nettoyer_images():
    """
    Supprime toutes les images temporaires.
    """

    nombre = 0

    if not DOSSIER_IMAGES.exists():
        return 0

    for fichier in DOSSIER_IMAGES.iterdir():

        if not fichier.is_file():
            continue

        try:
            fichier.unlink()
            nombre += 1

        except OSError:
            pass

    return nombre