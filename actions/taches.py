import os
import json

FICHIER_TACHES = "data/taches.json"


def charger_taches():
    """Charge toutes les tâches depuis le fichier JSON."""
    if not os.path.exists(FICHIER_TACHES):
        return []

    try:
        with open(FICHIER_TACHES, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def sauvegarder_taches(taches):
    """Sauvegarde les tâches dans le fichier JSON."""
    os.makedirs("data", exist_ok=True)

    with open(FICHIER_TACHES, "w", encoding="utf-8") as f:
        json.dump(taches, f, ensure_ascii=False, indent=2)


def ajouter_tache(texte):
    """Ajoute une nouvelle tâche."""

    texte = texte.strip()

    if not texte:
        return None

    taches = charger_taches()

    # ID unique
    nouvel_id = max(
        [t["id"] for t in taches],
        default=0
    ) + 1

    tache = {
        "id": nouvel_id,
        "texte": texte,
        "terminee": False
    }

    taches.append(tache)
    sauvegarder_taches(taches)

    return tache


def obtenir_taches():
    """Retourne toutes les tâches."""

    return charger_taches()


def terminer_tache(id_tache):
    """Marque une tâche comme terminée."""

    taches = charger_taches()

    for tache in taches:
        if tache["id"] == id_tache:
            tache["terminee"] = True
            sauvegarder_taches(taches)
            return tache

    return None


def annuler_tache(id_tache):
    """Remet une tâche comme non terminée."""

    taches = charger_taches()

    for tache in taches:
        if tache["id"] == id_tache:
            tache["terminee"] = False
            sauvegarder_taches(taches)
            return tache

    return None


def supprimer_tache(id_tache):
    """Supprime une tâche."""

    taches = charger_taches()

    nouvelles_taches = [
        tache
        for tache in taches
        if tache["id"] != id_tache
    ]

    if len(nouvelles_taches) == len(taches):
        return False

    sauvegarder_taches(nouvelles_taches)

    return True


def supprimer_taches_terminees():
    """Supprime toutes les tâches terminées."""

    taches = charger_taches()

    nouvelles_taches = [
        tache
        for tache in taches
        if not tache["terminee"]
    ]

    sauvegarder_taches(nouvelles_taches)

    return nouvelles_taches


def vider_taches():
    """Supprime toutes les tâches."""

    sauvegarder_taches([])

    return True