import os
import subprocess
import tempfile
from pathlib import Path

from PIL import Image


# ============================================================
# CONFIGURATION
# ============================================================

FORMATS_IMAGE = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".gif",
    ".tiff",
}

FORMATS_AUDIO_VIDEO = {
    ".mp3",
    ".wav",
    ".ogg",
    ".flac",
    ".m4a",
    ".aac",
    ".mp4",
    ".mkv",
    ".avi",
    ".mov",
    ".webm",
}

FORMATS_TEXTE = {
    ".txt",
}


# ============================================================
# DOSSIER TEMPORAIRE
# ============================================================

def creer_dossier_temporaire():
    """
    Crée un dossier temporaire pour une conversion.
    Le dossier est supprimé par le système après utilisation.
    """
    return tempfile.mkdtemp(prefix="deskbot_conversion_")


# ============================================================
# UTILITAIRES
# ============================================================

def normaliser_format(format_cible):
    """
    Transforme :
        png  -> .png
        .PNG -> .png
        JPG  -> .jpg
    """
    format_cible = str(format_cible).strip().lower()

    if not format_cible.startswith("."):
        format_cible = "." + format_cible

    return format_cible


def nom_sortie(fichier, format_cible):
    """
    Crée le nom du fichier converti.
    """
    fichier = Path(fichier)
    format_cible = normaliser_format(format_cible)

    return fichier.with_suffix(format_cible)


def verifier_ffmpeg():
    """
    Vérifie que FFmpeg est disponible sur la machine.
    """
    try:
        resultat = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )

        return resultat.returncode == 0

    except (
        FileNotFoundError,
        subprocess.SubprocessError,
        OSError
    ):
        return False

def convertir_gif_anime_vers_webp(fichier_entree, fichier_sortie):
    """
    Convertit un GIF animé en WebP animé
    en conservant toutes les frames, leur durée
    et le nombre de boucles.
    """

    fichier_entree = Path(fichier_entree)
    fichier_sortie = Path(fichier_sortie)

    frames = []
    durees = []

    with Image.open(fichier_entree) as gif:

        nombre_frames = getattr(
            gif,
            "n_frames",
            1
        )

        for numero_frame in range(nombre_frames):

            gif.seek(numero_frame)

            frame = gif.convert("RGBA").copy()

            frames.append(frame)

            duree = gif.info.get(
                "duration",
                100
            )

            durees.append(duree)

        if not frames:
            raise ValueError(
                "Le GIF ne contient aucune image."
            )

        boucle = gif.info.get(
            "loop",
            0
        )

    frames[0].save(
        fichier_sortie,
        "WEBP",
        save_all=True,
        append_images=frames[1:],
        duration=durees,
        loop=boucle,
        quality=95,
        method=6
    )

    return str(fichier_sortie)

# ============================================================
# CONVERSION IMAGE
# ============================================================

def convertir_image(fichier_entree, fichier_sortie):
    """
    Convertit une image avec Pillow.
    """

    fichier_entree = Path(fichier_entree)
    fichier_sortie = Path(fichier_sortie)

    with Image.open(fichier_entree) as image:

        format_sortie = fichier_sortie.suffix.lower()

        # JPEG ne supporte pas la transparence
        if format_sortie in {".jpg", ".jpeg"}:

            if image.mode in ("RGBA", "LA", "P"):
                image = image.convert("RGB")

            image.save(
                fichier_sortie,
                "JPEG",
                quality=95
            )

        elif format_sortie == ".png":

            image.save(
                fichier_sortie,
                "PNG"
            )

        elif format_sortie == ".webp":

            image.save(
                fichier_sortie,
                "WEBP",
                quality=95
            )

        elif format_sortie == ".bmp":

            image.save(
                fichier_sortie,
                "BMP"
            )

        elif format_sortie == ".gif":

            image.save(
                fichier_sortie,
                "GIF"
            )

        elif format_sortie == ".tiff":

            image.save(
                fichier_sortie,
                "TIFF"
            )

        else:
            raise ValueError(
                f"Format image non supporté : {format_sortie}"
            )

    return str(fichier_sortie)


# ============================================================
# CONVERSION AUDIO / VIDÉO
# ============================================================

def convertir_ffmpeg(fichier_entree, fichier_sortie):
    """
    Conversion audio/vidéo avec FFmpeg.
    """

    if not verifier_ffmpeg():
        raise RuntimeError(
            "FFmpeg n'est pas installé ou n'est pas disponible."
        )

    fichier_entree = Path(fichier_entree)
    fichier_sortie = Path(fichier_sortie)

    commande = [
        "ffmpeg",
        "-y",
        "-i",
        str(fichier_entree),
        str(fichier_sortie),
    ]

    resultat = subprocess.run(
        commande,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if resultat.returncode != 0:
        raise RuntimeError(
            "Erreur FFmpeg :\n" + resultat.stderr[-2000:]
        )

    if not fichier_sortie.exists():
        raise RuntimeError(
            "FFmpeg n'a pas créé le fichier de sortie."
        )

    return str(fichier_sortie)


# ============================================================
# TXT -> PDF
# ============================================================

def convertir_txt_pdf(fichier_entree, fichier_sortie):
    """
    Convertit un fichier TXT en PDF.
    """

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError:
        raise RuntimeError(
            "ReportLab n'est pas installé."
        )

    fichier_entree = Path(fichier_entree)
    fichier_sortie = Path(fichier_sortie)

    with open(
        fichier_entree,
        "r",
        encoding="utf-8",
        errors="replace"
    ) as fichier:
        lignes = fichier.readlines()

    largeur, hauteur = A4

    marge_gauche = 50
    marge_haut = 50
    marge_bas = 50

    taille_police = 10
    interligne = 14

    pdf = canvas.Canvas(
        str(fichier_sortie),
        pagesize=A4
    )

    y = hauteur - marge_haut

    pdf.setFont(
        "Helvetica",
        taille_police
    )

    for ligne in lignes:

        ligne = ligne.rstrip("\n")

        # Gestion simple des lignes trop longues
        largeur_max = 95

        morceaux = [
            ligne[i:i + largeur_max]
            for i in range(0, len(ligne), largeur_max)
        ]

        if not morceaux:
            morceaux = [""]

        for morceau in morceaux:

            if y < marge_bas:
                pdf.showPage()

                pdf.setFont(
                    "Helvetica",
                    taille_police
                )

                y = hauteur - marge_haut

            pdf.drawString(
                marge_gauche,
                y,
                morceau
            )

            y -= interligne

    pdf.save()

    return str(fichier_sortie)


# ============================================================
# CONVERSION PRINCIPALE
# ============================================================

def convertir_fichier(
    fichier_entree,
    format_cible,
    fichier_sortie=None
):
    """
    Fonction principale de conversion.

    Exemple :

        convertir_fichier(
            "photo.png",
            "jpg"
        )

    retourne le chemin du fichier converti.
    """

    fichier_entree = Path(fichier_entree)

    if not fichier_entree.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {fichier_entree}"
        )

    if not fichier_entree.is_file():
        raise ValueError(
            "Le chemin fourni n'est pas un fichier."
        )

    format_cible = normaliser_format(format_cible)

    extension_entree = fichier_entree.suffix.lower()

    if fichier_sortie is None:
        fichier_sortie = nom_sortie(
            fichier_entree,
            format_cible
        )
    else:
        fichier_sortie = Path(fichier_sortie)

    # --------------------------------------------------------
    # GIF ANIMÉ -> WEBP ANIMÉ
    # --------------------------------------------------------

    if (
        extension_entree == ".gif"
        and format_cible == ".webp"
    ):
        return convertir_gif_anime_vers_webp(
            fichier_entree,
            fichier_sortie
        )

    # --------------------------------------------------------
    # IMAGE
    # --------------------------------------------------------

    if (
        extension_entree in FORMATS_IMAGE
        and format_cible in FORMATS_IMAGE
    ):
        return convertir_image(
            fichier_entree,
            fichier_sortie
        )

    # --------------------------------------------------------
    # AUDIO / VIDEO
    # --------------------------------------------------------

    if (
        extension_entree in FORMATS_AUDIO_VIDEO
        and format_cible in FORMATS_AUDIO_VIDEO
    ):
        return convertir_ffmpeg(
            fichier_entree,
            fichier_sortie
        )

    # --------------------------------------------------------
    # TXT -> PDF
    # --------------------------------------------------------

    if (
        extension_entree == ".txt"
        and format_cible == ".pdf"
    ):
        return convertir_txt_pdf(
            fichier_entree,
            fichier_sortie
        )

    # --------------------------------------------------------
    # FORMAT IDENTIQUE
    # --------------------------------------------------------

    if extension_entree == format_cible:
        raise ValueError(
            "Le fichier est déjà dans ce format."
        )

    # --------------------------------------------------------
    # FORMAT NON SUPPORTÉ
    # --------------------------------------------------------

    raise ValueError(
        f"Conversion impossible : "
        f"{extension_entree} -> {format_cible}"
    )


# ============================================================
# FORMATS DISPONIBLES
# ============================================================

def obtenir_formats_disponibles():
    """
    Retourne les formats actuellement supportés.
    """

    return {
        "images": sorted(FORMATS_IMAGE),
        "audio_video": sorted(FORMATS_AUDIO_VIDEO),
        "texte": sorted(FORMATS_TEXTE),
        "texte_vers": [".pdf"],
    }


# ============================================================
# TEST RAPIDE
# ============================================================

if __name__ == "__main__":

    print("==========================================")
    print("       TEST CONVERTISSEUR DESKBOT")
    print("==========================================")

    print("\nFormats disponibles :")

    formats = obtenir_formats_disponibles()

    for categorie, valeurs in formats.items():
        print(f"\n{categorie} :")
        print("  " + ", ".join(valeurs))

    print("\n==========================================")
    print("Convertisseur prêt.")
    print("==========================================")