import json
import os
from datetime import datetime


FICHIER_NOTES = "data/notes.json"


# ---------------------------------------------------------
# Charger les notes
# ---------------------------------------------------------

def charger_notes():
    """Charge toutes les notes depuis le fichier JSON."""

    if not os.path.exists(FICHIER_NOTES):
        return {}

    try:
        with open(FICHIER_NOTES, "r", encoding="utf-8") as fichier:
            return json.load(fichier)

    except (json.JSONDecodeError, OSError):
        return {}


# ---------------------------------------------------------
# Sauvegarder les notes
# ---------------------------------------------------------

def sauvegarder_notes(notes):
    """Sauvegarde toutes les notes dans le fichier JSON."""

    dossier = os.path.dirname(FICHIER_NOTES)

    if dossier:
        os.makedirs(dossier, exist_ok=True)

    with open(FICHIER_NOTES, "w", encoding="utf-8") as fichier:
        json.dump(notes, fichier, ensure_ascii=False, indent=4)


# ---------------------------------------------------------
# Vérifier si une note existe
# ---------------------------------------------------------

def note_existe(titre):
    """Retourne True si la note existe."""

    notes = charger_notes()

    return titre.strip().lower() in notes


# ---------------------------------------------------------
# Créer une nouvelle note
# ---------------------------------------------------------

def creer_note(titre, texte=""):
    """Crée une nouvelle note."""

    titre = titre.strip()

    if not titre:
        return "Le titre de la note est vide."

    notes = charger_notes()

    cle = titre.lower()

    if cle in notes:
        return f"La note « {titre} » existe déjà."

    maintenant = datetime.now().isoformat()

    notes[cle] = {
        "titre": titre,
        "texte": texte.strip(),
        "date_creation": maintenant,
        "date_modification": maintenant
    }

    sauvegarder_notes(notes)

    return f"Note « {titre} » créée."


# ---------------------------------------------------------
# Ajouter du texte à une note
# ---------------------------------------------------------

def ajouter_texte(titre, texte):
    """Ajoute du texte à la fin d'une note."""

    titre = titre.strip()
    texte = texte.strip()

    if not titre:
        return "Le titre de la note est vide."

    if not texte:
        return "Le texte à ajouter est vide."

    notes = charger_notes()

    cle = titre.lower()

    if cle not in notes:
        return f"La note « {titre} » n'existe pas."

    if notes[cle]["texte"]:
        notes[cle]["texte"] += "\n" + texte
    else:
        notes[cle]["texte"] = texte

    notes[cle]["date_modification"] = datetime.now().isoformat()

    sauvegarder_notes(notes)

    return f"Texte ajouté à la note « {notes[cle]['titre']} »."


# ---------------------------------------------------------
# Remplacer le contenu d'une note
# ---------------------------------------------------------

def modifier_note(titre, texte):
    """Remplace entièrement le contenu d'une note."""

    titre = titre.strip()

    if not titre:
        return "Le titre de la note est vide."

    notes = charger_notes()

    cle = titre.lower()

    if cle not in notes:
        return f"La note « {titre} » n'existe pas."

    notes[cle]["texte"] = texte.strip()
    notes[cle]["date_modification"] = datetime.now().isoformat()

    sauvegarder_notes(notes)

    return f"Note « {notes[cle]['titre']} » modifiée."


# ---------------------------------------------------------
# Lire une note
# ---------------------------------------------------------

def lire_note(titre):
    """Retourne le contenu d'une note."""

    titre = titre.strip()

    notes = charger_notes()

    cle = titre.lower()

    if cle not in notes:
        return f"La note « {titre} » n'existe pas."

    note = notes[cle]

    if not note["texte"]:
        return f"La note « {note['titre']} » est vide."

    return note["texte"]


# ---------------------------------------------------------
# Supprimer une note
# ---------------------------------------------------------

def supprimer_note(titre):
    """Supprime une note."""

    titre = titre.strip()

    notes = charger_notes()

    cle = titre.lower()

    if cle not in notes:
        return f"La note « {titre} » n'existe pas."

    vrai_titre = notes[cle]["titre"]

    del notes[cle]

    sauvegarder_notes(notes)

    return f"Note « {vrai_titre} » supprimée."


# ---------------------------------------------------------
# Vider une note
# ---------------------------------------------------------

def vider_note(titre):
    """Supprime uniquement le contenu d'une note."""

    titre = titre.strip()

    notes = charger_notes()

    cle = titre.lower()

    if cle not in notes:
        return f"La note « {titre} » n'existe pas."

    notes[cle]["texte"] = ""
    notes[cle]["date_modification"] = datetime.now().isoformat()

    sauvegarder_notes(notes)

    return f"Note « {notes[cle]['titre']} » vidée."


# ---------------------------------------------------------
# Lister les notes
# ---------------------------------------------------------

def lister_notes():
    """Retourne la liste des notes."""

    notes = charger_notes()

    if not notes:
        return "Aucune note enregistrée."

    titres = [
        note["titre"]
        for note in notes.values()
    ]

    return "\n".join(
        f"- {titre}"
        for titre in titres
    )


# ---------------------------------------------------------
# Rechercher dans les notes
# ---------------------------------------------------------

def rechercher_notes(recherche):
    """Recherche un texte dans les titres et contenus."""

    recherche = recherche.strip().lower()

    if not recherche:
        return "Recherche vide."

    notes = charger_notes()

    resultats = []

    for note in notes.values():

        titre = note["titre"].lower()
        texte = note["texte"].lower()

        if recherche in titre or recherche in texte:
            resultats.append(note["titre"])

    if not resultats:
        return f"Aucune note trouvée pour « {recherche} »."

    return "\n".join(
        f"- {titre}"
        for titre in resultats
    )


# ---------------------------------------------------------
# Renommer une note
# ---------------------------------------------------------

def renommer_note(ancien_titre, nouveau_titre):
    """Renomme une note."""

    ancien_titre = ancien_titre.strip()
    nouveau_titre = nouveau_titre.strip()

    if not ancien_titre or not nouveau_titre:
        return "Le titre ne peut pas être vide."

    notes = charger_notes()

    ancienne_cle = ancien_titre.lower()
    nouvelle_cle = nouveau_titre.lower()

    if ancienne_cle not in notes:
        return f"La note « {ancien_titre} » n'existe pas."

    if nouvelle_cle in notes:
        return f"La note « {nouveau_titre} » existe déjà."

    note = notes[ancienne_cle]

    note["titre"] = nouveau_titre
    note["date_modification"] = datetime.now().isoformat()

    del notes[ancienne_cle]
    notes[nouvelle_cle] = note

    sauvegarder_notes(notes)

    return f"Note renommée en « {nouveau_titre} »."


# ---------------------------------------------------------
# Informations sur une note
# ---------------------------------------------------------

def informations_note(titre):
    """Retourne les informations d'une note."""

    titre = titre.strip()

    notes = charger_notes()

    cle = titre.lower()

    if cle not in notes:
        return f"La note « {titre} » n'existe pas."

    note = notes[cle]

    texte = note["texte"]

    nombre_caracteres = len(texte)
    nombre_mots = len(texte.split()) if texte else 0
    nombre_lignes = len(texte.splitlines()) if texte else 0

    return (
        f"Note : {note['titre']}\n"
        f"Créée le : {note['date_creation']}\n"
        f"Modifiée le : {note['date_modification']}\n"
        f"Nombre de mots : {nombre_mots}\n"
        f"Nombre de caractères : {nombre_caracteres}\n"
        f"Nombre de lignes : {nombre_lignes}"
    )