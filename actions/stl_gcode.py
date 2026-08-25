import os
import shutil
import subprocess
import tempfile
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

ORCA_SLICER = Path(
    r"C:\Program Files\OrcaSlicer\orca-slicer.exe"
)

ORCA_PROFILES = Path(
    r"C:\Program Files\OrcaSlicer\resources\profiles\Elegoo"
)

MACHINE_PROFILE = (
    ORCA_PROFILES
    / "machine"
    / "EN4SERIES"
    / "Elegoo Neptune 4 0.4 nozzle.json"
)

PROCESS_PROFILE = (
    ORCA_PROFILES
    / "process"
    / "EN4SERIES"
    / "0.20mm Standard @Elegoo N4 0.4 nozzle.json"
)

FILAMENT_PROFILE = (
    ORCA_PROFILES
    / "filament"
    / "EN4SERIES"
    / "Elegoo PLA @EN4 Series.json"
)


# ============================================================
# VERIFICATION
# ============================================================

def verifier_configuration():
    fichiers = {
        "OrcaSlicer": ORCA_SLICER,
        "Profil machine": MACHINE_PROFILE,
        "Profil processus": PROCESS_PROFILE,
        "Profil filament": FILAMENT_PROFILE,
    }

    for nom, chemin in fichiers.items():
        if not chemin.exists():
            raise FileNotFoundError(
                f"{nom} introuvable : {chemin}"
            )


# ============================================================
# STL → GCODE
# ============================================================

def convertir_stl_gcode(stl_source):
    """
    Convertit un fichier STL en G-code avec OrcaSlicer.

    Le STL et le G-code sont copiés/utilisés dans un dossier
    temporaire et supprimés automatiquement à la fin.

    Retourne le contenu du G-code sous forme de bytes.
    """

    verifier_configuration()

    stl_source = Path(stl_source)

    if not stl_source.exists():
        raise FileNotFoundError(
            f"Fichier STL introuvable : {stl_source}"
        )

    if stl_source.suffix.lower() != ".stl":
        raise ValueError(
            "Le fichier fourni doit être un fichier .stl"
        )

    # ========================================================
    # DOSSIER TEMPORAIRE
    # ========================================================

    with tempfile.TemporaryDirectory(
        prefix="deskbot_orca_"
    ) as temp_dir:

        temp_dir = Path(temp_dir)

        stl_dir = temp_dir / "stl"
        gcode_dir = temp_dir / "gcode"
        orca_data_dir = temp_dir / "orca_data"

        stl_dir.mkdir()
        gcode_dir.mkdir()
        orca_data_dir.mkdir()

        # ====================================================
        # COPIE DU STL
        # ====================================================

        stl_temp = stl_dir / stl_source.name

        shutil.copy2(
            stl_source,
            stl_temp
        )

        # ====================================================
        # COMMANDE ORCASLICER
        # ====================================================

        commande = [
            str(ORCA_SLICER),

            "--slice",
            "0",

            "--load-settings",
            str(MACHINE_PROFILE),

            "--load-settings",
            str(PROCESS_PROFILE),

            "--load-filaments",
            str(FILAMENT_PROFILE),

            "--outputdir",
            str(gcode_dir),

            str(stl_temp),
        ]

        print()
        print("=" * 50)
        print("       DESKBOT : STL → GCODE")
        print("=" * 50)

        print(f"STL : {stl_source}")
        print(f"Temporaire : {stl_temp}")
        print(f"Sortie temporaire : {gcode_dir}")

        print()
        print("Lancement d'OrcaSlicer...")
        print()

        # ====================================================
        # EXECUTION
        # ====================================================

        resultat = subprocess.run(
            commande,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        print("Code retour :", resultat.returncode)

        if resultat.stdout:
            print()
            print("--- SORTIE ORCASLICER ---")
            print(resultat.stdout)

        if resultat.stderr:
            print()
            print("--- ERREURS ORCASLICER ---")
            print(resultat.stderr)

        # ====================================================
        # VERIFICATION
        # ====================================================

        if resultat.returncode != 0:
            raise RuntimeError(
                "OrcaSlicer a échoué.\n\n"
                + resultat.stderr
            )

        # OrcaSlicer produit normalement plate_1.gcode
        fichiers_gcode = list(
            gcode_dir.glob("*.gcode")
        )

        if not fichiers_gcode:
            raise RuntimeError(
                "OrcaSlicer n'a généré aucun fichier G-code."
            )

        # On prend le premier G-code généré
        gcode_source = fichiers_gcode[0]

        print()
        print("G-code généré :")
        print(gcode_source)
        print(
            f"Taille : {gcode_source.stat().st_size:,} octets"
        )

        # ====================================================
        # LECTURE DU GCODE
        # ====================================================

        contenu = gcode_source.read_bytes()

        print()
        print("✅ Conversion STL → G-code réussie")
        print("🧹 Nettoyage des fichiers temporaires...")

        # Le TemporaryDirectory supprimera automatiquement :
        #
        # temp/
        # ├── stl/
        # ├── gcode/
        # └── orca_data/
        #
        # ainsi que tous les fichiers créés par OrcaSlicer.

        return contenu


# ============================================================
# VERSION QUI ÉCRIT DIRECTEMENT DANS UN FICHIER
# ============================================================

def convertir_stl_gcode_fichier(stl_source, destination):
    """
    Convertit un STL en G-code et écrit le résultat
    dans le fichier destination.

    Le STL temporaire et le G-code intermédiaire sont
    automatiquement supprimés.
    """

    contenu = convertir_stl_gcode(stl_source)

    destination = Path(destination)

    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    destination.write_bytes(contenu)

    return destination


# ============================================================
# TEST DIRECT
# ============================================================

if __name__ == "__main__":

    BASE_DIR = Path(__file__).resolve().parent.parent

    STL = BASE_DIR / "test.stl"

    if not STL.exists():
        print(
            f"❌ STL de test introuvable : {STL}"
        )
        raise SystemExit(1)

    try:

        gcode = convertir_stl_gcode(STL)

        print()
        print("=" * 50)
        print("🎉 TEST RÉUSSI")
        print("=" * 50)
        print()
        print(
            f"G-code généré en mémoire : "
            f"{len(gcode):,} octets"
        )

    except Exception as e:

        print()
        print("=" * 50)
        print("❌ ERREUR")
        print("=" * 50)
        print(e)