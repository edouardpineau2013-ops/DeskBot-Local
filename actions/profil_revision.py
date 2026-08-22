import os
import json
import random
from datetime import date, timedelta

FICHIER_PROFIL = "data/profil_revision.json"

COUT_BOITE = 20
RECOMPENSE_CONSOLATION = 3
BONUS_DOUBLON = 5


def charger_profil():
    if not os.path.exists(FICHIER_PROFIL):
        return {"points": 0, "collection": {}, "stats_matieres": {}}
    with open(FICHIER_PROFIL, "r", encoding="utf-8") as f:
        return json.load(f)


def sauvegarder_profil(profil):
    os.makedirs("data", exist_ok=True)
    with open(FICHIER_PROFIL, "w", encoding="utf-8") as f:
        json.dump(profil, f, ensure_ascii=False, indent=2)


def ajouter_points(n):
    profil = charger_profil()
    profil["points"] += n
    sauvegarder_profil(profil)


def ajouter_resultat_matiere(matiere, correcte):
    profil = charger_profil()
    profil["stats_matieres"].setdefault(matiere, {"correctes": 0, "tentatives": 0})
    profil["stats_matieres"][matiere]["tentatives"] += 1
    if correcte:
        profil["stats_matieres"][matiere]["correctes"] += 1
    sauvegarder_profil(profil)

def enregistrer_revision_terminee():
    profil = charger_profil()

    aujourd_hui = date.today()
    derniere_revision = profil.get("derniere_revision")

    if derniere_revision:
        derniere_revision = date.fromisoformat(derniere_revision)

    # Première révision
    if derniere_revision is None:
        profil["serie"] = 1

    # Révision déjà faite aujourd'hui
    elif derniere_revision == aujourd_hui:
        # La série ne change pas
        sauvegarder_profil(profil)
        return profil["serie"]

    # Révision faite hier : on continue la série
    elif derniere_revision == aujourd_hui - timedelta(days=1):
        profil["serie"] = profil.get("serie", 0) + 1

    # Un ou plusieurs jours ont été ratés
    else:
        profil["serie"] = 1

    profil["record_serie"] = max(
        profil.get("record_serie", 0),
        profil["serie"]
    )

    profil["derniere_revision"] = aujourd_hui.isoformat()

    sauvegarder_profil(profil)

    return profil["serie"]

SLUGS_PROFS = {
    "Prof d'Arts Plastiques": "prof_d_arts_plastiques",
    "Prof de Musique": "prof_de_musique",
    "Prof de Technologie": "prof_de_technologie",
    "Prof de Latin": "prof_de_latin",
    "Prof d'Allemand": "prof_d_allemand",
    "Prof de Sport": "prof_de_sport",
    "Prof de SVT": "prof_de_svt",
    "Prof de Physique-Chimie": "prof_de_physique_chimie",
    "Prof d'Anglais": "prof_d_anglais",
    "Prof d'Histoire Géo": "prof_d_histoire_geo",
    "Prof de Francais": "prof_de_francais",
    "Prof de Maths": "prof_de_maths",
}

def calculer_rarete_profs():
    raretes = {
        "Prof d'Arts Plastiques": "legendaire",
        "Prof de Musique": "legendaire",
        "Prof de Technologie": "legendaire",

        "Prof de Latin": "epique",
        "Prof d'Allemand": "epique",

        "Prof de Sport": "rare",
        "Prof de SVT": "rare",
        "Prof de Physique-Chimie": "rare",

        "Prof d'Anglais": "commun",
        "Prof d'Histoire Géo": "commun",
        "Prof de Francais": "commun",
        "Prof de Maths": "commun"
    }

    return {
        prof: {
            "rarete": rarete,
            "frequence": 1
        }
        for prof, rarete in raretes.items()
    }

CHANCES_RARETE = {
    "commun": 30,
    "rare": 15,
    "epique": 10,
    "legendaire": 5
}


def tirer_rarete():
    raretes = list(CHANCES_RARETE.keys())
    poids = list(CHANCES_RARETE.values())

    return random.choices(raretes, weights=poids, k=1)[0]


def ouvrir_boite_mystere():
    profil = charger_profil()

    if profil["points"] < COUT_BOITE:
        return {
            "succes": False,
            "erreur": "Pas assez de points"
        }

    profil["points"] -= COUT_BOITE

    tirage = random.random() * 100

    # 40 % : pas de skin
    if tirage < 40:
        profil["points"] += RECOMPENSE_CONSOLATION
        sauvegarder_profil(profil)

        return {
            "succes": True,
            "type": "consolation",
            "points_gagnes": RECOMPENSE_CONSOLATION
        }

    # 30 % : commun
    elif tirage < 70:
        rarete = "commun"

    # 15 % : rare
    elif tirage < 85:
        rarete = "rare"

    # 10 % : épique
    elif tirage < 95:
        rarete = "epique"

    # 5 % : légendaire
    else:
        rarete = "legendaire"

    rarete_profs = calculer_rarete_profs()

    profs_disponibles = [
        prof
        for prof, infos in rarete_profs.items()
        if infos["rarete"] == rarete
    ]

    prof_tire = random.choice(profs_disponibles)

    # Doublon
    if prof_tire in profil["collection"]:
        profil["points"] += BONUS_DOUBLON
        sauvegarder_profil(profil)

        return {
            "succes": True,
            "type": "doublon",
            "prof": prof_tire,
            "slug": SLUGS_PROFS[prof_tire],
            "rarete": rarete,
            "points_gagnes": BONUS_DOUBLON
        }

    # Nouveau skin
    profil["collection"][prof_tire] = rarete
    sauvegarder_profil(profil)

    return {
        "succes": True,
        "type": "skin",
        "prof": prof_tire,
        "slug": SLUGS_PROFS[prof_tire],
        "rarete": rarete
    }