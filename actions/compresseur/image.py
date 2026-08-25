from pathlib import Path
from PIL import Image


FORMATS_IMAGE = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".tiff",
    ".tif",
}


def compresser_image(source, destination):
    """
    Compresse une image en privilégiant la qualité.

    Retourne :
        {
            "taille_avant": ...,
            "taille_apres": ...,
            "format": ...,
            "reduction": ...
        }
    """

    source = Path(source)
    destination = Path(destination)

    destination.parent.mkdir(parents=True, exist_ok=True)

    taille_avant = source.stat().st_size

    with Image.open(source) as image:

        format_original = image.format
        extension = source.suffix.lower()

        # JPEG
        if extension in {".jpg", ".jpeg"}:

            # Conservation des métadonnées EXIF
            exif = image.info.get("exif", b"")

            image.save(
                destination,
                format="JPEG",
                quality=95,
                optimize=True,
                progressive=True,
                exif=exif
            )

        # PNG
        elif extension == ".png":

            image.save(
                destination,
                format="PNG",
                optimize=True,
                compress_level=9
            )

        # WEBP
        elif extension == ".webp":

            image.save(
                destination,
                format="WEBP",
                quality=95,
                method=6
            )

        # TIFF
        elif extension in {".tif", ".tiff"}:

            image.save(
                destination,
                format="TIFF",
                compression="tiff_lzw"
            )

        # BMP
        elif extension == ".bmp":

            # BMP est déjà peu compressible.
            image.save(
                destination,
                format="BMP"
            )

        else:
            raise ValueError(
                f"Format d'image non pris en charge : {extension}"
            )

    taille_apres = destination.stat().st_size

    # Si la compression a augmenté la taille,
    # on remet le fichier original.
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
        "format": format_original,
        "reduction": round(reduction, 2),
    }