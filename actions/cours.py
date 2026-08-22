import os
import json
import unicodedata
import re
from docx import Document
from actions.ia import extraire_fichier_avec_gemini

MIME_TYPES = {
    "pdf": "application/pdf",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
}

DOSSIER_COURS = "data/cours"
FICHIER_INDEX = "data/cours_index.json"


def slugifier(texte):
    texte = texte.lower().strip()
    texte = unicodedata.normalize("NFD", texte)
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    texte = re.sub(r"[^a-z0-9]+", "_", texte)
    return texte.strip("_")

def _extraire_texte_gemini(chemin_fichier, mime_type):

    prompt = (
        "Transcris fidèlement tout le texte et contenu important de ce document "
        "de cours scolaire, y compris s'il est manuscrit ou de qualité moyenne. "
        "Réponds uniquement avec le contenu transcrit, sans commentaire ni résumé."
    )

    resultat = extraire_fichier_avec_gemini(chemin_fichier, mime_type, prompt)

    if resultat is None:
        raise RuntimeError("Aucune clé Gemini disponible pour extraire ce fichier.")

    return resultat


def _extraire_texte_docx(chemin):
    document = Document(chemin)
    return "\n".join(p.text for p in document.paragraphs)


def _extraire_texte_txt(chemin):
    with open(chemin, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def extraire_texte(chemin_fichier):
    extension = chemin_fichier.lower().rsplit(".", 1)[-1]

    if extension == "docx":
        return _extraire_texte_docx(chemin_fichier)
    elif extension in ("txt", "md"):
        return _extraire_texte_txt(chemin_fichier)
    elif extension in MIME_TYPES:
        return _extraire_texte_gemini(chemin_fichier, MIME_TYPES[extension])
    else:
        raise ValueError(f"Format non supporté : .{extension}")


def _charger_index():
    if not os.path.exists(FICHIER_INDEX):
        return {}
    with open(FICHIER_INDEX, "r", encoding="utf-8") as f:
        return json.load(f)


def _sauvegarder_index(index):
    os.makedirs("data", exist_ok=True)
    with open(FICHIER_INDEX, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def importer_cours(matiere, chapitre, chemin_fichier_temporaire, nom_original):
    """Extrait le texte du fichier, le stocke, et met a jour l'index."""

    texte = extraire_texte(chemin_fichier_temporaire)

    matiere_slug = slugifier(matiere)
    chapitre_slug = slugifier(chapitre)

    dossier = os.path.join(DOSSIER_COURS, matiere_slug)
    os.makedirs(dossier, exist_ok=True)

    chemin_texte = os.path.join(dossier, f"{chapitre_slug}.txt")
    with open(chemin_texte, "w", encoding="utf-8") as f:
        f.write(texte)

    index = _charger_index()
    index.setdefault(matiere_slug, {"nom_affiche": matiere, "chapitres": {}})
    index[matiere_slug]["chapitres"][chapitre_slug] = {
        "nom_affiche": chapitre,
        "chemin": chemin_texte
    }
    _sauvegarder_index(index)

    return len(texte)


def lister_matieres():
    index = _charger_index()
    return [(v["nom_affiche"]) for v in index.values()]


def lister_chapitres(matiere):
    index = _charger_index()
    matiere_slug = slugifier(matiere)
    if matiere_slug not in index:
        return []
    return [c["nom_affiche"] for c in index[matiere_slug]["chapitres"].values()]


def obtenir_texte_chapitre(matiere, chapitre):
    index = _charger_index()
    matiere_slug = slugifier(matiere)
    chapitre_slug = slugifier(chapitre)

    if matiere_slug not in index:
        return None
    if chapitre_slug not in index[matiere_slug]["chapitres"]:
        return None

    chemin = index[matiere_slug]["chapitres"][chapitre_slug]["chemin"]

    with open(chemin, "r", encoding="utf-8") as f:
        return f.read()