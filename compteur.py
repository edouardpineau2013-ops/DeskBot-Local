import os
import re
from collections import defaultdict


# =========================================================
# CONFIGURATION
# =========================================================

DOSSIERS_IGNORES = {
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".env",
    "dist",
    "build",
    ".idea",
    ".vscode",
}

EXTENSIONS = {
    ".py": "Python",
    ".js": "JavaScript",
    ".css": "CSS",
    ".html": "HTML",
    ".htm": "HTML",
    ".json": "JSON",
    ".txt": "Texte",
    ".md": "Markdown",
    ".xml": "XML",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".bat": "Batch",
    ".ps1": "PowerShell",
    ".java": "Java",
    ".c": "C",
    ".h": "C/C++",
    ".cpp": "C++",
    ".hpp": "C++",
    ".cs": "C#",
    ".php": "PHP",
    ".sql": "SQL",
    ".sh": "Shell",
}


# =========================================================
# COMMENTAIRES
# =========================================================

COMMENTAIRES_LIGNE = {
    "Python": "#",
    "JavaScript": "//",
    "CSS": "//",
    "HTML": None,
    "JSON": None,
    "Texte": None,
    "Markdown": None,
    "XML": None,
    "YAML": "#",
    "Batch": "REM",
    "PowerShell": "#",
    "Java": "//",
    "C": "//",
    "C/C++": "//",
    "C++": "//",
    "C#": "//",
    "PHP": "//",
    "SQL": "--",
    "Shell": "#",
}


COMMENTAIRES_BLOC = {
    "Python": ('"""', "'''"),
    "JavaScript": ("/*", "*/"),
    "CSS": ("/*", "*/"),
    "HTML": ("<!--", "-->"),
    "XML": ("<!--", "-->"),
    "Java": ("/*", "*/"),
    "C": ("/*", "*/"),
    "C/C++": ("/*", "*/"),
    "C++": ("/*", "*/"),
    "C#": ("/*", "*/"),
    "PHP": ("/*", "*/"),
    "SQL": ("/*", "*/"),
    "Shell": ("/*", "*/"),
}


# =========================================================
# STATISTIQUES
# =========================================================

def creer_stats():
    return {
        "fichiers": 0,
        "lignes": 0,
        "vides": 0,
        "commentaires": 0,
        "code": 0,
        "caracteres": 0,
    }


def analyser_fichier(chemin, langage):
    stats = creer_stats()

    try:
        with open(chemin, "r", encoding="utf-8", errors="replace") as fichier:
            contenu = fichier.read()
    except Exception:
        return None

    stats["fichiers"] = 1
    stats["caracteres"] = len(contenu)

    lignes = contenu.splitlines()

    stats["lignes"] = len(lignes)

    bloc_de_commentaire = False
    debut_bloc = None
    fin_bloc = None

    if langage in COMMENTAIRES_BLOC:
        debut_bloc, fin_bloc = COMMENTAIRES_BLOC[langage]

    for ligne in lignes:

        ligne_strip = ligne.strip()

        # -------------------------------------------------
        # Ligne vide
        # -------------------------------------------------

        if not ligne_strip:
            stats["vides"] += 1
            continue

        # -------------------------------------------------
        # Commentaire bloc
        # -------------------------------------------------

        if debut_bloc and fin_bloc:

            if bloc_de_commentaire:

                stats["commentaires"] += 1

                if fin_bloc in ligne:
                    bloc_de_commentaire = False

                continue

            if ligne_strip.startswith(debut_bloc):

                stats["commentaires"] += 1

                if fin_bloc not in ligne_strip[len(debut_bloc):]:
                    bloc_de_commentaire = True

                continue

        # -------------------------------------------------
        # Commentaire ligne
        # -------------------------------------------------

        commentaire = COMMENTAIRES_LIGNE.get(langage)

        if commentaire:

            if ligne_strip.startswith(commentaire):
                stats["commentaires"] += 1
                continue

            # Cas particulier Batch
            if langage == "Batch":
                if ligne_strip.upper().startswith("REM "):
                    stats["commentaires"] += 1
                    continue

        # -------------------------------------------------
        # HTML / XML
        # -------------------------------------------------

        if langage in ("HTML", "XML"):

            if ligne_strip.startswith("<!--"):
                stats["commentaires"] += 1
                continue

        # -------------------------------------------------
        # Ligne de code
        # -------------------------------------------------

        stats["code"] += 1

    return stats


# =========================================================
# ANALYSE DU DOSSIER
# =========================================================

def analyser_dossier(dossier):
    resultats = defaultdict(creer_stats)

    fichiers_total = 0

    for racine, dossiers, fichiers in os.walk(dossier):

        # Ignore les dossiers inutiles
        dossiers[:] = [
            dossier
            for dossier in dossiers
            if dossier not in DOSSIERS_IGNORES
        ]

        for fichier in fichiers:

            extension = os.path.splitext(fichier)[1].lower()

            if extension not in EXTENSIONS:
                continue

            langage = EXTENSIONS[extension]

            chemin = os.path.join(racine, fichier)

            stats = analyser_fichier(chemin, langage)

            if stats is None:
                continue

            fichiers_total += 1

            for cle in stats:
                resultats[langage][cle] += stats[cle]

    return resultats, fichiers_total


# =========================================================
# AFFICHAGE
# =========================================================

def afficher_ligne(langage, stats):

    print(
        f"{langage:<15}"
        f"{stats['fichiers']:>10}"
        f"{stats['vides']:>12}"
        f"{stats['commentaires']:>15}"
        f"{stats['code']:>12}"
        f"{stats['lignes']:>12}"
        f"{stats['caracteres']:>15}"
    )


def afficher_resultats(resultats):

    total = creer_stats()

    print()
    print("=" * 100)
    print("                         COMPTEUR DE CODE")
    print("=" * 100)
    print()

    print(
        f"{'Langage':<15}"
        f"{'Fichiers':>10}"
        f"{'Vides':>12}"
        f"{'Commentaires':>15}"
        f"{'Code':>12}"
        f"{'Lignes':>12}"
        f"{'Caractères':>15}"
    )

    print("-" * 100)

    # Tri par nombre de lignes de code
    langages = sorted(
        resultats.items(),
        key=lambda x: x[1]["code"],
        reverse=True
    )

    for langage, stats in langages:

        afficher_ligne(langage, stats)

        for cle in total:
            total[cle] += stats[cle]

    print("-" * 100)

    afficher_ligne("TOTAL", total)

    print("=" * 100)

    print()
    print("📊 Résumé")
    print()
    print(f"📁 Fichiers analysés : {total['fichiers']}")
    print(f"📏 Lignes totales   : {total['lignes']}")
    print(f"💻 Lignes de code   : {total['code']}")
    print(f"💬 Commentaires      : {total['commentaires']}")
    print(f"⬜ Lignes vides      : {total['vides']}")
    print(f"🔤 Caractères        : {total['caracteres']}")
    print()


# =========================================================
# PROGRAMME PRINCIPAL
# =========================================================

def main():

    print()
    print("==========================================")
    print("        COMPTEUR DE PROJET DESKBOT")
    print("==========================================")
    print()

    dossier = input(
        "📂 Chemin du dossier à analyser : "
    ).strip().strip('"')

    if not dossier:
        print("\n❌ Aucun dossier indiqué.")
        return

    if not os.path.isdir(dossier):
        print()
        print("❌ Ce dossier n'existe pas.")
        print()
        return

    print()
    print("🔎 Analyse en cours...")
    print()

    resultats, fichiers_total = analyser_dossier(dossier)

    if not resultats:
        print("❌ Aucun fichier compatible trouvé.")
        return

    afficher_resultats(resultats)


if __name__ == "__main__":
    main()