from pathlib import Path
import subprocess
import shutil


FORMATS_VIDEO = {
    ".mp4",
    ".mov",
    ".mkv",
    ".avi",
    ".webm",
    ".m4v",
}


def ffmpeg_disponible():
    return shutil.which("ffmpeg") is not None


def compresser_video(source, destination):
    """
    Compression vidéo haute qualité avec FFmpeg.
    """

    source = Path(source)
    destination = Path(destination)

    destination.parent.mkdir(parents=True, exist_ok=True)

    if not ffmpeg_disponible():
        raise RuntimeError(
            "FFmpeg n'est pas installé sur le serveur."
        )

    taille_avant = source.stat().st_size

    commande = [
        "ffmpeg",
        "-y",

        "-i",
        str(source),

        # Vidéo
        "-c:v",
        "libx264",

        # Qualité élevée
        "-crf",
        "18",

        # Compression efficace
        "-preset",
        "slow",

        # Conservation de la résolution et du framerate
        "-fps_mode",
        "passthrough",

        # Audio
        "-c:a",
        "aac",

        "-b:a",
        "192k",

        # Compatibilité MP4
        "-movflags",
        "+faststart",

        str(destination),
    ]

    resultat = subprocess.run(
        commande,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if resultat.returncode != 0:
        raise RuntimeError(
            "Erreur FFmpeg :\n" + resultat.stderr[-3000:]
        )

    if not destination.exists():
        raise RuntimeError(
            "FFmpeg n'a pas créé le fichier final."
        )

    taille_apres = destination.stat().st_size

    # Si le résultat est plus gros,
    # on considère que la compression n'est pas intéressante.
    if taille_apres >= taille_avant:
        destination.write_bytes(source.read_bytes())
        taille_apres = taille_avant

    reduction = (
        (1 - taille_apres / taille_avant) * 100
        if taille_avant
        else 0
    )

    return {
        "taille_avant": taille_avant,
        "taille_apres": taille_apres,
        "reduction": round(reduction, 2),
        "codec": "H.264",
        "crf": 18,
    }