from pathlib import Path
import shutil
import uuid

from .image import compresser_image, FORMATS_IMAGE
from .video import compresser_video, FORMATS_VIDEO
from .pdf import compresser_pdf


FORMAT_PDF = {".pdf"}


def creer_dossier_temporaire(base="temp/compresseur"):
    dossier = Path(base) / str(uuid.uuid4())
    dossier.mkdir(parents=True, exist_ok=True)
    return dossier


def detecter_type(fichier):
    extension = Path(fichier).suffix.lower()

    if extension in FORMATS_IMAGE:
        return "image"

    if extension in FORMATS_VIDEO:
        return "video"

    if extension in FORMAT_PDF:
        return "pdf"

    return None


def compresser_fichier(source, destination=None):
    """
    Détecte automatiquement le type du fichier
    puis applique la compression adaptée.
    """

    source = Path(source)

    if not source.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {source}"
        )

    type_fichier = detecter_type(source)

    if type_fichier is None:
        raise ValueError(
            f"Format non pris en charge : {source.suffix}"
        )

    if destination is None:
        dossier = creer_dossier_temporaire()

        destination = (
            dossier /
            f"{source.stem}_compressed{source.suffix}"
        )

    destination = Path(destination)

    if type_fichier == "image":
        resultat = compresser_image(
            source,
            destination
        )

    elif type_fichier == "video":
        resultat = compresser_video(
            source,
            destination
        )

    elif type_fichier == "pdf":
        resultat = compresser_pdf(
            source,
            destination
        )

    else:
        raise ValueError(
            "Type de fichier non pris en charge."
        )

    resultat["source"] = str(source)
    resultat["destination"] = str(destination)
    resultat["type"] = type_fichier

    return resultat


def supprimer_temporaire(dossier):
    """
    Supprime complètement un dossier temporaire.
    """

    dossier = Path(dossier)

    if dossier.exists():
        shutil.rmtree(
            dossier,
            ignore_errors=True
        )