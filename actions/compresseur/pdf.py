from pathlib import Path
import pikepdf


def compresser_pdf(source, destination):
    """
    Optimisation PDF en privilégiant la conservation de qualité.
    """

    source = Path(source)
    destination = Path(destination)

    destination.parent.mkdir(parents=True, exist_ok=True)

    taille_avant = source.stat().st_size

    with pikepdf.open(source) as pdf:

        pdf.save(
            destination,
            compress_streams=True,
            recompress_flate=True,
            object_stream_mode=pikepdf.ObjectStreamMode.generate
        )

    taille_apres = destination.stat().st_size

    # Ne jamais remplacer un fichier par une version plus grosse.
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
    }