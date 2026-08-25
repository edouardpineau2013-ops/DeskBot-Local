from pathlib import Path
import subprocess
import os


# =========================================================
# ORCASLICER
# =========================================================

ORCA_DIR = Path(
    r"C:\Program Files\OrcaSlicer\orca-slicer.exe"
)

ORCA_EXE = ORCA_DIR / "OrcaSlicer.exe"


# =========================================================
# DESKBOT
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DOSSIER_GCODE = (
    BASE_DIR
    / "data"
    / "gcode"
)

DOSSIER_GCODE.mkdir(
    parents=True,
    exist_ok=True
)


# =========================================================
# VÉRIFICATION
# =========================================================

def verifier_orca():

    if not ORCA_EXE.exists():
        raise FileNotFoundError(
            f"OrcaSlicer introuvable :\n{ORCA_EXE}"
        )


# =========================================================
# STL → GCODE
# =========================================================

def convertir_stl_en_gcode(
    fichier_stl,
    fichier_gcode=None
):

    verifier_orca()

    fichier_stl = Path(fichier_stl)

    if not fichier_stl.exists():
        raise FileNotFoundError(
            f"Fichier STL introuvable :\n{fichier_stl}"
        )

    if fichier_stl.suffix.lower() != ".stl":
        raise ValueError(
            "Le fichier fourni n'est pas un fichier STL."
        )


    # -----------------------------------------------------
    # Fichier GCODE
    # -----------------------------------------------------

    if fichier_gcode is None:

        fichier_gcode = (
            DOSSIER_GCODE
            / f"{fichier_stl.stem}.gcode"
        )

    else:

        fichier_gcode = Path(
            fichier_gcode
        )


    fichier_gcode.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    # -----------------------------------------------------
    # Affichage
    # -----------------------------------------------------

    print()
    print("========================================")
    print("      DESKBOT - IMPRESSION 3D")
    print("========================================")
    print()

    print(f"STL        : {fichier_stl}")
    print(f"GCODE      : {fichier_gcode}")
    print("Imprimante : Neptune 4")
    print()

    print("Lancement d'OrcaSlicer...")
    print()


    # -----------------------------------------------------
    # Commande OrcaSlicer
    # -----------------------------------------------------

    commande = [
        str(ORCA_EXE),

        "--slice",

        "--output",
        str(fichier_gcode),

        str(fichier_stl)
    ]


    # -----------------------------------------------------
    # Environnement
    # -----------------------------------------------------

    environnement = os.environ.copy()


    # -----------------------------------------------------
    # Exécution
    # -----------------------------------------------------

    resultat = subprocess.run(
        commande,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environnement
    )


    # -----------------------------------------------------
    # Logs
    # -----------------------------------------------------

    if resultat.stdout:
        print(resultat.stdout)

    if resultat.stderr:
        print(resultat.stderr)


    # -----------------------------------------------------
    # Erreur
    # -----------------------------------------------------

    if resultat.returncode != 0:

        raise RuntimeError(
            "OrcaSlicer a rencontré une erreur.\n\n"
            f"Code retour : {resultat.returncode}\n\n"
            f"Sortie :\n{resultat.stdout}\n\n"
            f"Erreur :\n{resultat.stderr}"
        )


    # -----------------------------------------------------
    # Vérification
    # -----------------------------------------------------

    if not fichier_gcode.exists():

        raise RuntimeError(
            "OrcaSlicer s'est terminé sans générer "
            "de fichier G-code."
        )


    # -----------------------------------------------------
    # Succès
    # -----------------------------------------------------

    print()
    print("========================================")
    print("      G-CODE GÉNÉRÉ AVEC SUCCÈS")
    print("========================================")
    print()

    print(fichier_gcode)

    return str(fichier_gcode)