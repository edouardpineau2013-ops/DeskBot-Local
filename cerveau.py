from rapidfuzz import process, fuzz
import re
from datetime import datetime, timedelta
from villes import VILLES
from actions.heure import heure
from actions.calcul import calculer
from actions.systeme import executer
from actions.meteo import meteo, meteo_ici, extraire_jour_cible, JOURS_SEMAINE
from actions.chronometre import chronometre
from actions.minuteur import minuteur
from actions.alarme import definir_alarme, supprimer_alarme_principale, prochaine_alarme, obtenir_alarme_principale, activer_desactiver_alarme, definir_sonnerie, SONNERIES_DISPONIBLES
from commandes import trouver_commande, ALIAS_VILLES, extraire_url
from actions.musique import jouer_musique, arreter_musique, pause_musique, volume_musique, augmenter_volume, diminuer_volume
from actions.mail import etat_mails_non_lus
from actions.recherche import rechercher_paragraphe, rechercher_resultat
from actions.youtube import obtenir_stats_chaine
from actions.trajet import calculer_trajet
from actions.pronote import obtenir_emploi_du_temps, obtenir_devoirs, obtenir_moyenne_generale, obtenir_profs_absents
from actions.revision import session_revision
from actions.taches import ajouter_tache, obtenir_taches, terminer_tache, annuler_tache, supprimer_tache, vider_taches, supprimer_taches_terminees
from actions.question_ia import generer_reponse_avec_groq
from actions.convertisseur import convertir
from actions.traduction import traiter_traduction
from actions.notifications import creer_notification
from actions.agenda import ajouter_evenement, obtenir_evenements, prochains_evenements, rechercher_evenement, supprimer_evenement, modifier_evenement, formater_evenement
from actions.agenda_url import ajouter_evenement_depuis_url
from actions.divertissement import divertissement, devinette_en_cours, verifier_devinette
from actions.hasard import pile_ou_face, lancer_de, nombre_aleatoire, choix_aleatoire
from actions.notes import creer_note, ajouter_texte, lire_note, modifier_note, supprimer_note, vider_note, renommer_note, lister_notes, rechercher_notes
from actions.ia import resumer_avec_groq
from actions.correction import corriger_texte



def extraire_texte_correction(texte):
    texte = texte.strip()

    prefixes = [
        "corrige ce texte",
        "corriger ce texte",
        "corrige le texte",
        "corriger le texte",
        "corrige moi ce texte",
        "corriger moi ce texte",
        "corrige-moi ce texte",
        "corriger-moi ce texte",
    ]

    texte_lower = texte.lower()

    for prefixe in prefixes:
        if texte_lower.startswith(prefixe):
            return texte[len(prefixe):].strip(" :")

    return ""

def extraire_texte_resume(texte):
    texte = texte.strip()

    prefixes = [
        "fais-moi un résumé de ce texte",
        "fais moi un résumé de ce texte",
        "fais-moi un résumé de texte",
        "fais moi un résumé de texte",
        "résume ce texte",
        "resume ce texte",
        "résume le texte",
        "resume le texte",
        "résume",
        "resume",
    ]

    texte_lower = texte.lower()

    for prefixe in prefixes:
        if texte_lower.startswith(prefixe):
            return texte[len(prefixe):].strip()

    return texte

# ---------------------------------------------------------
# Extraire le titre d'une note
# ---------------------------------------------------------

def extraire_titre_note(texte):
    texte = texte.strip()

    motifs = [
        r"(?:ma note|la note)\s+(.+?)(?:\s+avec\s+|\s+contenant\s+|\s*:\s*)",
        r"(?:ma note|la note)\s+(.+)$"
    ]

    for motif in motifs:
        resultat = re.search(motif, texte, re.IGNORECASE)

        if resultat:
            return resultat.group(1).strip()

    return None


# ---------------------------------------------------------
# Créer une note
# ---------------------------------------------------------

def traiter_creer_note(texte):
    texte = texte.strip()

    match = re.search(
        r"(?:crée|créer|ajoute|ajouter)\s+une\s+note\s+(.+)",
        texte,
        re.IGNORECASE
    )

    if not match:
        return "Quel est le titre de la note ?"

    contenu = match.group(1).strip()

    # Recherche d'un contenu après "avec"
    match_avec = re.match(
        r"(.+?)\s+avec\s+(.+)",
        contenu,
        re.IGNORECASE
    )

    if match_avec:
        titre = match_avec.group(1).strip()
        texte_note = match_avec.group(2).strip()

        return creer_note(titre, texte_note)

    return creer_note(contenu)


# ---------------------------------------------------------
# Ajouter du texte
# ---------------------------------------------------------

def traiter_ajouter_note(texte):
    texte = texte.strip()

    match = re.search(
        r"(?:ajoute|ajouter|rajoute|rajouter|complete|completer)\s+"
        r"(.+?)\s+"
        r"(?:a|dans)\s+"
        r"(?:ma|la)\s+note\s+"
        r"(.+)",
        texte,
        re.IGNORECASE
    )

    if not match:
        return "Je n'ai pas compris quoi ajouter à la note."

    texte_a_ajouter = match.group(1).strip()
    titre = match.group(2).strip()

    return ajouter_texte(titre, texte_a_ajouter)


# ---------------------------------------------------------
# Lire une note
# ---------------------------------------------------------

def traiter_lire_note(texte):
    match = re.search(
        r"(?:lis|lire|affiche|afficher|montre|montrer)\s+"
        r"(?:ma|la)\s+note\s+(.+)",
        texte,
        re.IGNORECASE
    )

    if not match:
        return "Quelle note veux-tu lire ?"

    titre = match.group(1).strip()

    contenu = lire_note(titre)

    return f"Note « {titre} » :\n{contenu}"


# ---------------------------------------------------------
# Modifier une note
# ---------------------------------------------------------

def traiter_modifier_note(texte):
    match = re.search(
        r"(?:modifie|modifier)\s+(?:ma|la)\s+note\s+(.+?)"
        r"\s+avec\s+(.+)",
        texte,
        re.IGNORECASE
    )

    if not match:
        return "Indique le nom de la note et son nouveau contenu."

    titre = match.group(1).strip()
    nouveau_texte = match.group(2).strip()

    return modifier_note(titre, nouveau_texte)


# ---------------------------------------------------------
# Supprimer une note
# ---------------------------------------------------------

def traiter_supprimer_note(texte):
    match = re.search(
        r"(?:supprime|supprimer|efface|effacer)\s+"
        r"(?:ma|la)\s+note\s+(.+)",
        texte,
        re.IGNORECASE
    )

    if not match:
        return "Quelle note veux-tu supprimer ?"

    titre = match.group(1).strip()

    return supprimer_note(titre)


# ---------------------------------------------------------
# Vider une note
# ---------------------------------------------------------

def traiter_vider_note(texte):
    match = re.search(
        r"(?:vide|vider)\s+(?:ma|la)\s+note\s+(.+)",
        texte,
        re.IGNORECASE
    )

    if not match:
        return "Quelle note veux-tu vider ?"

    titre = match.group(1).strip()

    return vider_note(titre)


# ---------------------------------------------------------
# Renommer une note
# ---------------------------------------------------------

def traiter_renommer_note(texte):
    match = re.search(
        r"(?:renomme|renommer)\s+(?:ma|la)\s+note\s+(.+?)"
        r"\s+en\s+(.+)",
        texte,
        re.IGNORECASE
    )

    if not match:
        return "Indique l'ancien et le nouveau nom de la note."

    ancien_titre = match.group(1).strip()
    nouveau_titre = match.group(2).strip()

    return renommer_note(ancien_titre, nouveau_titre)


# ---------------------------------------------------------
# Lister les notes
# ---------------------------------------------------------

def traiter_lister_notes():
    return lister_notes()


# ---------------------------------------------------------
# Rechercher dans les notes
# ---------------------------------------------------------

def traiter_rechercher_notes(texte):
    match = re.search(
        r"(?:cherche|chercher|recherche|rechercher)\s+"
        r"dans\s+mes\s+notes\s+(.+)",
        texte,
        re.IGNORECASE
    )

    if not match:
        return "Que veux-tu rechercher dans tes notes ?"

    recherche = match.group(1).strip()

    return rechercher_notes(recherche)

def extraire_bornes_hasard(texte):
    correspondance = re.search(
        r"entre\s+(-?\d+)\s+et\s+(-?\d+)",
        texte.lower()
    )

    if correspondance:
        minimum = int(correspondance.group(1))
        maximum = int(correspondance.group(2))
        return minimum, maximum

    return 1, 100


def extraire_choix_hasard(texte):
    texte = texte.lower().strip()

    correspondance = re.search(
        r"entre\s*:?\s*(.+)",
        texte
    )

    if not correspondance:
        return []

    contenu = correspondance.group(1)

    # Remplace " et " par une virgule
    contenu = re.sub(r"\s+et\s+", ",", contenu)

    # Sépare les choix avec les virgules
    choix = [
        element.strip()
        for element in contenu.split(",")
        if element.strip()
    ]

    return choix

def extraire_faces_de(texte):
    texte = texte.lower()

    # "dé à 20 faces", "dé de 20 faces"
    correspondance = re.search(r"d[ée]\s+(?:à|de)\s+(\d+)\s+faces?", texte)
    if correspondance:
        return int(correspondance.group(1))

    # "dé 20 faces"
    correspondance = re.search(r"d[ée]\s+(\d+)\s+faces?", texte)
    if correspondance:
        return int(correspondance.group(1))

    # "d20"
    correspondance = re.search(r"\bd(\d+)\b", texte)
    if correspondance:
        return int(correspondance.group(1))

    return 6

def extraire_titre_agenda(texte):

    titre = texte.strip().lower()

    # Retirer les débuts de commande
    prefixes = [
        # AJOUT
        "ajoute un événement",
        "ajoute un evenement",
        "ajoute un évenement",
        "ajouter un événement",
        "ajouter un evenement",
        "ajouter un évenement",
        "crée un événement",
        "cree un evenement",
        "créer un événement",
        "creer un evenement",
        "crée un évenement",
        "cree un évenement",
        "programme un événement",
        "programme un evenement",
        "programme un évenement",
        "planifie un événement",
        "planifie un evenement",
        "planifie un évenement",
        "ajoute un rendez-vous",
        "ajoute un rendez vous",
        "ajouter un rendez-vous",
        "ajouter un rendez vous",
        "crée un rendez-vous",
        "cree un rendez vous",
        "programme un rendez-vous",
        "programme un rendez vous",

        # MODIFICATION
        "modifie l'événement",
        "modifie l'evenement",
        "modifie l'évenement",
        "modifier l'événement",
        "modifier l'evenement",
        "modifier l'évenement",
        "modifie événement",
        "modifie evenement",
        "modifie évenement",
        "modifier événement",
        "modifier evenement",
        "modifier évenement",

        "modifie le rendez-vous",
        "modifie le rendez vous",
        "modifier le rendez-vous",
        "modifier le rendez vous",

        # SUPPRESSION
        "supprime l'événement",
        "supprime l'evenement",
        "supprime l'évenement",
        "supprimer l'événement",
        "supprimer l'evenement",
        "supprimer l'évenement",
        "supprime événement",
        "supprime evenement",
        "supprime évenement",
        "supprimer événement",
        "supprimer evenement",
        "supprimer évenement",

        "supprime le rendez-vous",
        "supprime le rendez vous",
        "supprimer le rendez-vous",
        "supprimer le rendez vous",
    ]

    for prefixe in prefixes:
        if titre.startswith(prefixe):
            titre = titre[len(prefixe):].strip()
            break

    # Retirer l'heure
    titre = re.sub(
        r"\bà\s+\d{1,2}"
        r"(?:\s*(?:h|heure|heures)\s*\d{1,2})?"
        r"(?:\s*minutes?)?",
        "",
        titre
    )

    # Retirer les dates du type "le 14 août" ou "14 août"
    mois = [
        "janvier",
        "février",
        "fevrier",
        "mars",
        "avril",
        "mai",
        "juin",
        "juillet",
        "août",
        "aout",
        "septembre",
        "octobre",
        "novembre",
        "décembre",
        "decembre"
    ]

    mois_regex = "|".join(mois)

    titre = re.sub(
        rf"\b(?:le\s+)?\d{{1,2}}\s+(?:{mois_regex})(?:\s+\d{{4}})?\b",
        "",
        titre
    )

    # Retirer les dates relatives
    for mot in [
        "aujourd'hui",
        "aujourd hui",
        "demain",
        "après-demain",
        "apres-demain",
        "apres demain"
    ]:
        titre = titre.replace(mot, "")

    # Retirer les dates au format JJ/MM/AAAA
    titre = re.sub(
        r"\b\d{1,2}/\d{1,2}/\d{4}\b",
        "",
        titre
    )

    # Retirer les jours
    for jour in [
        "lundi",
        "mardi",
        "mercredi",
        "jeudi",
        "vendredi",
        "samedi",
        "dimanche"
    ]:
        titre = re.sub(
            rf"\b{jour}\b",
            "",
            titre
        )

    # Agenda / calendrier
    titre = re.sub(
        r"\b(?:dans mon agenda|sur mon agenda|dans le calendrier|sur le calendrier|agenda)\b",
        "",
        titre
    )

    # Nettoyage
    titre = re.sub(r"\s+", " ", titre)
    titre = titre.strip(" ,.-")

    return titre


def extraire_heure_agenda(texte):

    texte = texte.lower()

    # 14 heures 25 minutes
    match = re.search(
        r"\bà\s*(\d{1,2})\s*(?:heures?|h)\s+(\d{1,2})\s*(?:minutes?)?\b",
        texte
    )

    if match:
        heures = int(match.group(1))
        minutes = int(match.group(2))

        if heures > 23 or minutes > 59:
            return None

        return heures, minutes

    # 14h25 / 14 h 25
    match = re.search(
        r"\bà\s*(\d{1,2})\s*h\s*(\d{1,2})\b",
        texte
    )

    if match:
        heures = int(match.group(1))
        minutes = int(match.group(2))

        if heures > 23 or minutes > 59:
            return None

        return heures, minutes

    # 14 heures / 14h
    match = re.search(
        r"\bà\s*(\d{1,2})\s*(?:heures?|h)\b",
        texte
    )

    if match:
        heures = int(match.group(1))

        if heures > 23:
            return None

        return heures, 0

    return None

def extraire_date_agenda(texte):

    maintenant = datetime.now()
    texte = texte.lower()

    # Date au format JJ/MM/AAAA
    correspondance = re.search(
        r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b",
        texte
    )

    if correspondance:

        jour = int(correspondance.group(1))
        mois = int(correspondance.group(2))
        annee = int(correspondance.group(3))

        try:

            date = datetime(
                annee,
                mois,
                jour
            )

            return date.strftime("%Y-%m-%d")

        except ValueError:

            return maintenant.strftime("%Y-%m-%d")

    # Date du type "14 août" ou "le 14 août"
    mois = {
        "janvier": 1,
        "février": 2,
        "fevrier": 2,
        "mars": 3,
        "avril": 4,
        "mai": 5,
        "juin": 6,
        "juillet": 7,
        "août": 8,
        "aout": 8,
        "septembre": 9,
        "octobre": 10,
        "novembre": 11,
        "décembre": 12,
        "decembre": 12
    }

    correspondance = re.search(
        r"\b(?:le\s+)?(\d{1,2})\s+"
        r"(janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|"
        r"septembre|octobre|novembre|décembre|decembre)"
        r"(?:\s+(\d{4}))?\b",
        texte
    )

    if correspondance:

        jour = int(correspondance.group(1))
        nom_mois = correspondance.group(2)
        annee = (
            int(correspondance.group(3))
            if correspondance.group(3)
            else maintenant.year
        )

        mois_numero = mois[nom_mois]

        try:

            date = datetime(
                annee,
                mois_numero,
                jour
            )

            return date.strftime("%Y-%m-%d")

        except ValueError:

            return maintenant.strftime("%Y-%m-%d")


    if (
        "après-demain" in texte
        or "apres-demain" in texte
        or "apres demain" in texte
    ):
        return (
            maintenant + timedelta(days=2)
        ).strftime("%Y-%m-%d")


    if "demain" in texte:
        return (
            maintenant + timedelta(days=1)
        ).strftime("%Y-%m-%d")


    if (
        "aujourd'hui" in texte
        or "aujourd hui" in texte
    ):
        return maintenant.strftime("%Y-%m-%d")


    jours = {
        "lundi": 0,
        "mardi": 1,
        "mercredi": 2,
        "jeudi": 3,
        "vendredi": 4,
        "samedi": 5,
        "dimanche": 6
    }


    for nom_jour, numero_jour in jours.items():

        if nom_jour in texte:

            jours_a_ajouter = (
                numero_jour - maintenant.weekday()
            ) % 7

            if jours_a_ajouter == 0:
                jours_a_ajouter = 7

            return (
                maintenant + timedelta(days=jours_a_ajouter)
            ).strftime("%Y-%m-%d")


    return maintenant.strftime("%Y-%m-%d")

def verification_journaliere():
    # Heure actuelle
    heure_actuelle = heure()

    # Météo ici
    if datetime.now().hour <= 17:
        meteo = meteo_ici()
    else:
        meteo = meteo_ici(1)

    # Mails non lus
    nombre_mails, details_mails = etat_mails_non_lus()

    # Tâches restantes
    taches = obtenir_taches()
    taches_restantes = [
        tache for tache in taches
        if not tache.get("terminee", False)
    ]

    # Construction de la réponse
    reponse = f"{heure_actuelle}. "

    if datetime.now().hour <= 17:
        reponse += f"{meteo} "
    else:
        reponse += f"Demain, {meteo} "

    if nombre_mails == 0:
        reponse += "Tu n'as aucun mail non lu. "
    elif nombre_mails == 1:
        reponse += "Tu as 1 mail non lu. "
    else:
        reponse += f"Tu as {nombre_mails} mails non lus. "

    if not taches_restantes:
        reponse += "Tu n'as aucune tâche restante."
    elif len(taches_restantes) == 1:
        reponse += (
            f"Il te reste une tâche : "
            f"{taches_restantes[0]['texte']}."
        )
    else:
        reponse += f"Il te reste {len(taches_restantes)} tâches : "

        textes = [
            tache["texte"]
            for tache in taches_restantes
        ]

        reponse += ", ".join(textes) + "."

    return reponse

def extraire_infos_notification(texte):
    MOIS = {
        "janvier": 1,
        "février": 2,
        "fevrier": 2,
        "mars": 3,
        "avril": 4,
        "mai": 5,
        "juin": 6,
        "juillet": 7,
        "août": 8,
        "aout": 8,
        "septembre": 9,
        "octobre": 10,
        "novembre": 11,
        "décembre": 12,
        "decembre": 12
    }

    maintenant = datetime.now()

    jour = maintenant.day
    mois = maintenant.month
    heure = maintenant.hour
    minute = maintenant.minute

    texte_original = texte
    texte = texte.lower().strip()

    # --------------------------------------------
    # JOUR + MOIS
    # Exemple : "le 15 juin"
    # --------------------------------------------

    match = re.search(
        r"\ble\s+(\d{1,2})\s+("
        + "|".join(MOIS.keys())
        + r")\b",
        texte
    )

    if match:
        jour = int(match.group(1))
        mois = MOIS[match.group(2)]

    else:
        # Jour seul : "le 15"
        match = re.search(r"\ble\s+(\d{1,2})\b", texte)

        if match:
            jour = int(match.group(1))

        # Mois seul : "en juin"
        match = re.search(
            r"\b(?:en|au mois de|le mois de)\s+("
            + "|".join(MOIS.keys())
            + r")\b",
            texte
        )

        if match:
            mois = MOIS[match.group(1)]

    # --------------------------------------------
    # HEURE
    # --------------------------------------------
    # Reconnaît :
    # "à 17 heures 30"
    # "à 17 heure 30"
    # "à 17h30"
    # "à 17 h 30"
    # "à 17 heures"
    # "à 17h"
    #
    # IMPORTANT : heures/heure avant h
    # --------------------------------------------

    match = re.search(
        r"\bà\s+(\d{1,2})"
        r"(?:\s*(?:heures|heure|h)\s*(\d{1,2})?)?",
        texte
    )

    if match:
        heure = int(match.group(1))

        if match.group(2):
            minute = int(match.group(2))
        else:
            minute = 0

    # --------------------------------------------
    # RETIRER LE PRÉFIXE
    # --------------------------------------------

    contenu = texte_original

    contenu = re.sub(
        r"^\s*programme\s+une\s+notification\s*",
        "",
        contenu,
        flags=re.IGNORECASE
    )

    # --------------------------------------------
    # RETIRER LE JOUR + MOIS
    # --------------------------------------------

    contenu = re.sub(
        r"\ble\s+\d{1,2}\s+(?:"
        + "|".join(MOIS.keys())
        + r")\b",
        "",
        contenu,
        flags=re.IGNORECASE
    )

    # --------------------------------------------
    # RETIRER LE JOUR SEUL
    # --------------------------------------------

    contenu = re.sub(
        r"\ble\s+\d{1,2}\b",
        "",
        contenu,
        flags=re.IGNORECASE
    )

    # --------------------------------------------
    # RETIRER LE MOIS SEUL
    # --------------------------------------------

    contenu = re.sub(
        r"\b(?:en|au mois de|le mois de)\s+(?:"
        + "|".join(MOIS.keys())
        + r")\b",
        "",
        contenu,
        flags=re.IGNORECASE
    )

    # --------------------------------------------
    # RETIRER L'HEURE
    # --------------------------------------------

    contenu = re.sub(
        r"\bà\s+\d{1,2}"
        r"(?:\s*(?:heures|heure|h)\s*\d{1,2})?",
        "",
        contenu,
        flags=re.IGNORECASE
    )

    contenu = contenu.strip(" ,.-")

    return jour, mois, heure, minute, contenu

def extraire_conversion(texte):
    texte = texte.strip()

    prefixes = (
        "convertis",
        "convertir",
        "conversion de",
        "fais la conversion de",
        "fais-moi la conversion de",
        "fait la conversion de",
        "converti",
    )

    texte_normalise = texte.lower()

    for prefixe in prefixes:
        if texte_normalise.startswith(prefixe):
            return texte[len(prefixe):].strip()

    return texte


def extraire_repeter(texte):
    prefixes = (
        "répète après-moi",
        "répète après moi",
        "repete après-moi",
        "repete après moi",
        "répète",
        "répeter",
        "repeter",
        "après-moi",
        "après moi",
    )

    texte = texte.strip()

    for prefixe in prefixes:
        if texte.lower().startswith(prefixe):
            return texte[len(prefixe):].strip()

    return texte

def extraire_questions_ia(texte):
    prefixe = "demande à l'ia", "pose à l'ia", "ia", "intelligence artificielle"
    if texte.lower().startswith(prefixe):
        return texte[len(prefixe):].strip()
    return texte

def extraire_id_tache(texte):
    match = re.search(
        r"(?:tache|taches|tâche|tâches)\s+(?:numero|numéro)?\s*(\d+)",
        texte.lower()
    )

    if match:
        return int(match.group(1))

    return None

def extraire_tache_todo(texte, action):
    texte = texte.lower().strip()

    morceaux = [
        "à ma todo",
        "a ma todo",
        "dans ma todo",
        "dans la todo",
        "de ma todo",
        "de la todo",
        "à ma to do",
        "a ma to do",
        "dans ma to do",
        "de ma to do"
    ]

    for morceau in morceaux:
        texte = texte.replace(morceau, "")

    if action == "ajouter":
        mots = [
            "ajoute",
            "ajouter",
            "rajoute",
            "rajouter",
            "mets"
        ]
    elif action == "terminer":
        mots = [
            "termine",
            "terminer",
            "j'ai terminé",
            "jai termine",
            "fini",
            "finie",
            "fait",
            "faite"
        ]
    elif action == "supprimer":
        mots = [
            "supprime",
            "supprimer",
            "enleve",
            "enlever",
            "retire",
            "retirer"
        ]
    else:
        mots = []

    for mot in mots:
        texte = texte.replace(mot, "", 1)

    texte = texte.strip(" ,.!?")

    texte = texte.strip('"').strip("'").strip()

    return texte

def extraire_matiere_chapitre(texte):
    match = re.search(r"en\s+(.+?)\s+sur\s+(.+)$", texte)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None, None

def formater_duree(duree_minutes):
    total_minutes = round(duree_minutes)
    jours, reste = divmod(total_minutes, 24 * 60)
    heures, minutes = divmod(reste, 60)

    morceaux = []
    if jours:
        morceaux.append(f"{jours} jour" + ("s" if jours > 1 else ""))
    if heures:
        morceaux.append(f"{heures} heure" + ("s" if heures > 1 else ""))
    if minutes or not morceaux:
        morceaux.append(f"{minutes} minute" + ("s" if minutes > 1 else ""))

    if len(morceaux) == 1:
        return morceaux[0]
    return ", ".join(morceaux[:-1]) + " et " + morceaux[-1]

def extraire_trajet(texte):
    match = re.search(r"de (.+?)\s+(?:a|à)\s+(.+?)(?:\s+(?:en|a|à)\s+(voiture|velo|vélo|pied))?$", texte)
    if not match:
        return None, None, "voiture"

    depart = match.group(1).strip()
    arrivee = match.group(2).strip()
    mode_brut = match.group(3)

    mode = "en voiture"
    if mode_brut:
        if "elo" in mode_brut or "élo" in mode_brut:
            mode = "en velo"
        elif "pied" in mode_brut:
            mode = "à pied"

    return depart, arrivee, mode

def extraire_nom_chaine(texte):
    for mot in ["statistiques youtube de", "statistique youtube de", "stats youtube de"]:
        if mot in texte:
            reste = texte.split(mot, 1)[1].strip()
            return reste if reste else None
    return None

def extraire_requete_recherche(texte):
    t = texte

    for mot in ["recherche sur google", "recherche google", "cherche sur google",
                "cherche google", "recherche", "cherche", "google"]:
        t = t.replace(mot, "")

    numero = None
    match = re.search(r"resultat\s*(\d)", t)

    if match:
        numero = int(match.group(1))
        t = t[:match.start()]

    return t.strip(), numero

def extraire_volume(texte):
    match = re.search(r"(\d{1,3})\s*(?:pour cent|%)?", texte)
    if match:
        return int(match.group(1))
    return None

def extraire_duree(texte):
    minutes = 0
    secondes = 0

    m = re.search(r"(\d+)\s*minutes?", texte)
    s = re.search(r"(\d+)\s*secondes?", texte)

    if m:
        minutes = int(m.group(1))
    if s:
        secondes = int(s.group(1))

    return minutes, secondes


def extraire_heure(texte):
    match = re.search(r"(\d{1,2})\s*h(?:eures?)?\s*(\d{1,2})?", texte)

    if not match:
        return None

    heures = int(match.group(1))
    minutes = int(match.group(2)) if match.group(2) else 0

    if heures > 23 or minutes > 59:
        return None

    return heures, minutes

def extraire_numero_sonnerie(texte):
    match = re.search(r"(\d)", texte)
    if match:
        return int(match.group(1))
    return None

def extraire_jours(texte):
    return [i for i, jour in enumerate(JOURS_SEMAINE) if jour in texte]

def traiter_commande(texte):

    texte_original = texte.strip()
    texte = texte_original.lower()

    if session_revision.active:

        if "arrete" in texte and ("revision" in texte or "reviser" in texte):
            session_revision.arreter()
            return "Révision arrêtée."

        correcte, explication = session_revision.repondre(texte)

        reponse = "Bonne réponse ! " if correcte else "Ce n'est pas tout à fait ça. "
        reponse += explication + " "

        question_suivante = session_revision.question_suivante()

        if question_suivante is None:
            stats = session_revision.stats()
            reponse += (
                f"Révision terminée ! {stats['nb_correctes']} bonnes réponses sur "
                f"{stats['nb_tentatives']} tentatives, {stats['pourcentage_premier_coup']} "
                f"pour cent de réussite du premier coup."
            )
        else:
            reponse += "Question suivante : " + question_suivante

        return reponse

    if devinette_en_cours():
        return verifier_devinette(texte)

    commande = trouver_commande(texte)

    print("Commande reconnue :", commande)
    
    commande = trouver_commande(texte)

    print("Texte :", texte)
    print("Commande :", commande)

    if commande == "bonjour":
        return "Bonjour !"

    elif commande == "merci":
        return "De rien !"

    elif commande == "ça_va":
        return "Je vais très bien."

    elif commande == "qui_es_tu":
        return "Je suis DeskBot, votre assistant personnel."

    elif commande == "heure":
        return heure()

    elif commande == "meteo":

        if "ici" in texte or "chez moi" in texte:
            return meteo_ici()

        jour_offset = extraire_jour_cible(texte)  # AVANT tout nettoyage

        texte_ville = re.sub(r"\d{4}-\d{2}-\d{2}", "", texte).strip()
        mots = texte_ville.split()

        ville = "Paris"

        ville_alias = None
        for nom_ville, alias in ALIAS_VILLES.items():
            if any(a in texte_ville for a in alias):
                ville_alias = nom_ville
                break

        if ville_alias:
            ville = ville_alias

        elif "à" in mots:
            ville = " ".join(mots[mots.index("à") + 1:])

        elif "a" in mots:
            ville = " ".join(mots[mots.index("a") + 1:])

        print("Ville :", ville)

        resultat = process.extractOne(ville, VILLES, scorer=fuzz.ratio, score_cutoff=70)

        if resultat:
            ville = resultat[0]

        if jour_offset:
            return meteo(ville, jour_offset)

        return meteo(ville)
    
    elif commande == "musique":
        return jouer_musique(texte)

    elif commande == "stop_musique":
        return arreter_musique()

    elif commande == "pause_musique":
        return pause_musique()

    elif commande == "augmenter_volume":
        return augmenter_volume()

    elif commande == "diminuer_volume":
        return diminuer_volume()

    elif commande == "regler_volume":
        valeur = extraire_volume(texte)
        if valeur is None:
            return "Je n'ai pas compris le volume souhaité."
        return volume_musique(valeur)

    elif commande == "demarrer_chronometre":

        if chronometre.demarrer():
            return "Chronomètre démarré."
        else:
            return "Le chronomètre est déjà en cours."
        
    elif commande == "temps_chronometre":

        return "Le chronomètre indique : " + chronometre.texte()
    
    elif commande == "pause_chronometre":

        if chronometre.pause():
            return "Chronomètre en pause."
        else:
            return "Le chronomètre n'est pas en cours."
        
    elif commande == "reprendre_chronometre":

        if chronometre.reprendre():
            return "Chronomètre repris."
        else:
            return "Le chronomètre n'est pas en pause."
        
    elif commande == "arreter_chronometre":

        if chronometre.arreter():
            return "Chronomètre arrêté."
        else:
            return "Le chronomètre n'est pas démarré."
        
    elif commande == "reinitialiser_chronometre":

        chronometre.reinitialiser()
        return "Chronomètre remis à zéro."
    
    elif commande == "demarrer_minuteur":
        minutes, secondes = extraire_duree(texte)
        if minuteur.demarrer(minutes, secondes):
            return f"Minuteur démarré pour {minutes} minutes et {secondes} secondes."
        return "Un minuteur est déjà en cours, ou la durée n'est pas valide."

    elif commande == "arreter_minuteur":
        if minuteur.arreter():
            return "Minuteur arrêté."
        return "Aucun minuteur en cours."

    elif commande == "pause_minuteur":
        if minuteur.pause():
            return "Minuteur en pause."
        return "Le minuteur n'est pas en cours."

    elif commande == "reprendre_minuteur":
        if minuteur.reprendre():
            return "Minuteur repris."
        return "Le minuteur n'est pas en pause."

    elif commande == "ajouter_alarme":
        resultat = extraire_heure(texte)
        if resultat is None:
            return "Je n'ai pas compris l'heure de l'alarme."
        h, m = resultat
        jours = extraire_jours(texte)
        definir_alarme(h, m, jours)
        if jours:
            noms = ", ".join(JOURS_SEMAINE[j] for j in jours)
            return f"Alarme programmée à {h} heures {m}, les {noms}."
        return f"Alarme programmée à {h} heures {m}, tous les jours."

    elif commande == "supprimer_alarmes":
        supprimer_alarme_principale()
        return "L'alarme a été supprimée."

    elif commande == "allumer_alarme":
        alarme = obtenir_alarme_principale()
        if alarme is None:
            return "Aucune alarme n'est programmée."
        if not alarme.get("active", False):
            activer_desactiver_alarme()
        return "Alarme activée."

    elif commande == "eteindre_alarme":
        alarme = obtenir_alarme_principale()
        if alarme is None:
            return "Aucune alarme n'est programmée."
        if alarme.get("active", False):
            activer_desactiver_alarme()
        return "Alarme désactivée."

    elif commande == "sonnerie_alarme":
        numero = extraire_numero_sonnerie(texte)
        cle = f"alarme{numero}" if numero else None
        if cle is None or cle not in SONNERIES_DISPONIBLES:
            return "Je n'ai pas compris quelle sonnerie choisir."
        if not definir_sonnerie(SONNERIES_DISPONIBLES[cle]):
            return "Aucune alarme n'est programmée pour lui assigner une sonnerie."
        return f"Sonnerie réglée sur alarme {numero}."
    
    elif commande == "temps_minuteur":
        if not minuteur.actif:
            return "Aucun minuteur en cours."
        s = minuteur.temps_restant()
        return f"Il reste {s // 60} minutes et {s % 60} secondes."

    elif commande == "temps_alarme":
        delta = prochaine_alarme()
        if delta is None:
            return "Aucune alarme programmée."
        h = delta.seconds // 3600
        m = (delta.seconds % 3600) // 60
        return f"La prochaine alarme sonne dans {h} heures et {m} minutes."

    elif commande == "verifier_mails":
        total, details = etat_mails_non_lus(max_details=5)

        if total == 0:
            return "Vous n'avez aucun mail non lu."

        phrases = [f"{expediteur} : {sujet}" for expediteur, sujet in details]
        reponse = "Vous avez 1 mail non lu." if total == 1 else f"Vous avez {total} mails non lus."

        if total > len(details):
            reponse += f" Voici les {len(details)} premiers : " + " ; ".join(phrases)
        else:
            reponse += " " + " ; ".join(phrases)

        return reponse

    elif commande == "recherche_paragraphe":
        requete, _ = extraire_requete_recherche(texte)
        if not requete:
            return "Je n'ai pas compris ce que tu veux que je recherche."
        resultat = rechercher_paragraphe(requete)
        if resultat is None:
            return f"Je n'ai pas trouvé de résumé pour {requete}."
        return resultat

    elif commande == "recherche_resultat":
        requete, numero = extraire_requete_recherche(texte)
        if not requete or numero is None:
            return "Je n'ai pas compris quelle recherche ni quel résultat tu veux."
        resultat = rechercher_resultat(requete, numero)
        if resultat is None:
            return f"Je n'ai pas trouvé de {numero}e résultat pour {requete}."
        titre, url = resultat
        return f"{numero}e résultat : {titre}."

    elif commande == "stats_youtube":
        nom_chaine = extraire_nom_chaine(texte)
        handle = nom_chaine if nom_chaine else "@ElectronicCode"

        stats = obtenir_stats_chaine(handle, par_handle=True)

        if stats is None:
            return "Je n'ai pas trouvé cette chaîne YouTube."

        abonnes_txt = f"{stats['abonnes']} d'abonnés" if stats['abonnes'] is not None else "un nombre d'abonnés masqué"

        if stats["vues"] <= 1000:
            vues_arrondies = stats["vues"]
        elif stats["vues"] <= 100000:
            vues_arrondies = round(stats["vues"] / 100) * 100
        elif stats["vues"] <= 100000000:
            vues_arrondies = round(stats["vues"] / 100000) * 100000
        elif stats["vues"] <= 100000000000:
            vues_arrondies = round(stats["vues"] / 100000000) * 100000000
        elif stats["vues"] <= 100000000000000:
            vues_arrondies = round(stats["vues"] / 100000000000) * 100000000000
        elif stats["vues"] <= 100000000000000000:
            vues_arrondies = round(stats["vues"] / 100000000000000) * 100000000000000

        vues_txt = f"{vues_arrondies:,}".replace(",", " ")

        return (
            f"La chaîne {stats['nom']} a {abonnes_txt}, "
            f"{vues_txt} de vues au total, et {stats['videos']} vidéos."
        )

    elif commande == "calculer_trajet":
        depart, arrivee, mode = extraire_trajet(texte)

        if depart is None or arrivee is None:
            return "Je n'ai pas compris le départ et l'arrivée du trajet."

        resultat = calculer_trajet(depart, arrivee, mode)

        if resultat is None:
            return "Je n'ai pas réussi à calculer ce trajet."

        distance_km, duree_minutes = resultat
        duree_texte = formater_duree(duree_minutes)

        return (
            f"Le trajet de {depart} à {arrivee} fait {distance_km:.1f} kilomètres, "
            f"soit environ {duree_texte} {mode}."
        )

    elif commande == "pronote_emploi_du_temps":
        cours = obtenir_emploi_du_temps()
        if cours is None:
            return "Je n'ai pas réussi à me connecter à Pronote."
        if not cours:
            return "Aucun cours aujourd'hui."
        phrases = [f"{c['matiere']} de {c['debut']} à {c['fin']}" + (" (annulé)" if c['annule'] else "") for c in cours]
        return "Aujourd'hui : " + " ; ".join(phrases)

    elif commande == "pronote_devoirs":
        devoirs = obtenir_devoirs()
        if devoirs is None:
            return "Je n'ai pas réussi à me connecter à Pronote."
        if not devoirs:
            return "Aucun devoir à venir."
        phrases = [f"{d['matiere']} pour le {d['date']}" for d in devoirs]
        return "Tu as : " + " ; ".join(phrases)

    elif commande == "pronote_notes":
        moyenne = obtenir_moyenne_generale()
        if moyenne is None:
            return "Je n'ai pas réussi à récupérer ta moyenne."
        return f"Ta moyenne générale est de {moyenne} sur 20."

    elif commande == "pronote_absents":
        absents = obtenir_profs_absents()
        if absents is None:
            return "Je n'ai pas réussi à me connecter à Pronote."
        if not absents:
            return "Aucun professeur absent aujourd'hui."
        phrases = [f"{c['matiere']} de {c['debut']} à {c['fin']}" for c in absents]
        return "Cours annulés aujourd'hui : " + " ; ".join(phrases)

    elif commande == "ajouter_todo":

        tache_texte = extraire_tache_todo(texte, "ajouter")

        if not tache_texte:
            return "Je n'ai pas compris quelle tâche ajouter."

        tache = ajouter_tache(tache_texte)

        if tache is None:
            return "Je n'ai pas réussi à ajouter cette tâche."

        return f"Tâche ajoutée : {tache['texte']}."

    elif commande == "afficher_todo":

        taches = obtenir_taches()

        if not taches:
            return "Ta liste de tâches est vide."

        non_terminees = [
            tache for tache in taches
            if not tache["terminee"]
        ]

        terminees = [
            tache for tache in taches
            if tache["terminee"]
        ]

        if not non_terminees:
            return "Toutes tes tâches sont terminées."

        phrases = [
            f"{i + 1}. {tache['texte']}"
            for i, tache in enumerate(non_terminees)
        ]

        return (
            f"Tu as {len(non_terminees)} tâche"
            + ("s" if len(non_terminees) > 1 else "")
            + " à faire : "
            + " ; ".join(phrases)
        )

    elif commande == "terminer_todo":

        tache_id = extraire_id_tache(texte)

        taches = obtenir_taches()

        if not taches:
            return "Ta liste de tâches est vide."

        # --------------------------------------------
        # Recherche par ID
        # --------------------------------------------

        if tache_id is not None:

            tache_trouvee = next(
                (t for t in taches if t["id"] == tache_id),
                None
            )

            if tache_trouvee is None:
                return f"Je n'ai pas trouvé la tâche numéro {tache_id}."

            if tache_trouvee["terminee"]:
                return f"La tâche {tache_trouvee['texte']} est déjà terminée."

            terminer_tache(tache_trouvee["id"])

            return f"Tâche terminée : {tache_trouvee['texte']}."

        # --------------------------------------------
        # Sinon recherche par texte
        # --------------------------------------------

        tache_texte = extraire_tache_todo(texte, "terminer")

        if not tache_texte:
            return "Je n'ai pas compris quelle tâche terminer."

        tache_trouvee = None

        for tache in taches:
            if tache["texte"].lower() == tache_texte.lower():
                tache_trouvee = tache
                break

        if tache_trouvee is None:
            for tache in taches:
                if tache_texte.lower() in tache["texte"].lower():
                    tache_trouvee = tache
                    break

        if tache_trouvee is None:
            return f"Je n'ai pas trouvé la tâche {tache_texte}."

        if tache_trouvee["terminee"]:
            return f"La tâche {tache_trouvee['texte']} est déjà terminée."

        terminer_tache(tache_trouvee["id"])

        return f"Tâche terminée : {tache_trouvee['texte']}."

    elif commande == "supprimer_todo":

        taches = obtenir_taches()

        if not taches:
            return "Ta liste de tâches est vide."

        # --------------------------------------------
        # Recherche par ID
        # --------------------------------------------

        tache_id = extraire_id_tache(texte)

        if tache_id is not None:

            tache_trouvee = next(
                (t for t in taches if t["id"] == tache_id),
                None
            )

            if tache_trouvee is None:
                return f"Je n'ai pas trouvé la tâche numéro {tache_id}."

            supprimer_tache(tache_trouvee["id"])

            return f"Tâche supprimée : {tache_trouvee['texte']}."

        # --------------------------------------------
        # Sinon recherche par texte
        # --------------------------------------------

        tache_texte = extraire_tache_todo(texte, "supprimer")

        if not tache_texte:
            return "Je n'ai pas compris quelle tâche supprimer."

        tache_trouvee = None

        for tache in taches:
            if tache["texte"].lower() == tache_texte.lower():
                tache_trouvee = tache
                break

        if tache_trouvee is None:
            for tache in taches:
                if tache_texte.lower() in tache["texte"].lower():
                    tache_trouvee = tache
                    break

        if tache_trouvee is None:
            return f"Je n'ai pas trouvé la tâche {tache_texte}."

        supprimer_tache(tache_trouvee["id"])

        return f"Tâche supprimée : {tache_trouvee['texte']}."

    elif commande == "vider_todo":

        taches = obtenir_taches()

        if not taches:
            return "Ta liste de tâches est déjà vide."

        vider_taches()

        return "Ta liste de tâches a été vidée."

    elif commande == "supprimer_taches_terminees":

        taches = obtenir_taches()

        if not taches:
            return "Ta liste de tâches est déjà vide."

        avant = len(taches)

        taches_restantes = [
            tache for tache in taches
            if not tache["terminee"]
        ]

        if len(taches_restantes) == avant:
            return "Aucune tâche terminée à supprimer."

        supprimer_taches_terminees()

        nombre = avant - len(taches_restantes)

        return (
            f"{nombre} tâche supprimée."
            if nombre == 1
            else f"{nombre} tâches supprimées."
        )

    elif commande == "annule_todo":
        match = re.search(r"(?:tâche|tache)\s*(\d+)", texte.lower())

        if match:
            id_tache = int(match.group(1))
            tache = annuler_tache(id_tache)

            if tache:
                reponse = f"Tâche annulée : {tache['texte']}."
            else:
                reponse = f"Je n'ai pas trouvé la tâche {id_tache}."
        else:
            reponse = "Quelle tâche veux-tu annuler ?"

        return reponse

    elif commande == "question_ia":
        question = extraire_questions_ia(texte)
        reponse = generer_reponse_avec_groq(question)
        return reponse

    elif commande == "session_revision":
        jouer_musique("lofi pour travailler")

        minuteur.demarrer_pomodoro()

        return "Session de révision lancée. Minuteur pomodoro démarré."

    elif commande == "repeter":
        repeter = extraire_repeter(texte)
        return repeter

    elif commande == "calculer":
        return calculer(texte)

    elif commande == "convertir":
        conversion = extraire_conversion(texte)
        return convertir(conversion)

    elif commande == "traduire":
        return traiter_traduction(texte)

    elif commande == "notification":
        jour, mois, heure_notification, minute, contenu = extraire_infos_notification(texte)

        creer_notification(
            jour,
            mois,
            heure_notification,
            minute,
            contenu
        )

        print(jour, mois, heure_notification, minute, contenu)
        return "La notification a été créee !"

    # =====================================================
    # GOOGLE AGENDA
    # =====================================================

    elif commande == "ajouter_agenda_url":

        url = extraire_url(texte_original)

        if not url:
            return "Je n'ai pas trouvé de lien dans ta commande."

        try:
            resultat = ajouter_evenement_depuis_url(url)

            return resultat["message"]

        except Exception as e:
            print("Erreur ajout agenda depuis URL :", e)
            return "Je n'ai pas réussi à récupérer l'événement depuis ce site."

    elif commande == "ajouter_agenda":

        date = extraire_date_agenda(texte)
        heure_resultat = extraire_heure_agenda(texte)

        if heure_resultat is None:
            return "Je n'ai pas compris l'heure du rendez-vous."

        h, m = heure_resultat

        titre = extraire_titre_agenda(texte)

        if not titre:
            return "Je n'ai pas compris le titre de l'événement."

        heure_debut = f"{h:02d}:{m:02d}"

        try:

            evenement = ajouter_evenement(
                titre=titre,
                date=date,
                heure_debut=heure_debut,
                duree_minutes=60
            )

            return (
                f"Événement ajouté : {titre}, "
                f"le {datetime.strptime(date, '%Y-%m-%d').strftime('%d/%m/%Y')} "
                f"à {heure_debut}."
            )

        except Exception as e:

            print("Erreur Google Agenda :", e)

            return "Je n'ai pas réussi à ajouter l'événement."

    elif commande == "afficher_agenda":

        date = extraire_date_agenda(texte)

        try:

            evenements = obtenir_evenements(
                date=date,
                nombre_max=20
            )

        except Exception as e:

            print("Erreur Google Agenda :", e)

            return "Je n'ai pas réussi à consulter ton agenda."

        if not evenements:
            return "Tu n'as aucun événement ce jour-là."

        phrases = [
            formater_evenement(evenement)
            for evenement in evenements
        ]

        return (
            f"Voici ton agenda : "
            + " ; ".join(phrases)
        )

    elif commande == "prochains_agenda":

        try:

            evenements = prochains_evenements(5)

        except Exception as e:

            print("Erreur Google Agenda :", e)

            return "Je n'ai pas réussi à consulter ton agenda."

        if not evenements:
            return "Tu n'as aucun événement à venir."

        phrases = [
            formater_evenement(evenement)
            for evenement in evenements
        ]

        return (
            "Voici tes prochains événements : "
            + " ; ".join(phrases)
        )

    elif commande == "supprimer_agenda":

        # On cherche les événements correspondant au texte
        recherche = extraire_titre_agenda(texte)

        if not recherche:
            return "Je n'ai pas compris quel événement supprimer."

        try:

            evenements = rechercher_evenement(
                recherche,
                nombre_max=10
            )

        except Exception as e:

            print("Erreur Google Agenda :", e)

            return "Je n'ai pas réussi à consulter ton agenda."

        if not evenements:
            return (
                f"Je n'ai pas trouvé d'événement correspondant à {recherche}."
            )

        if len(evenements) > 1:
            phrases = [
                f"{i + 1}. {formater_evenement(e)}"
                for i, e in enumerate(evenements)
            ]

            return (
                "J'ai trouvé plusieurs événements : "
                + " ; ".join(phrases)
                + ". Précise lequel supprimer."
            )

        evenement = evenements[0]

        try:

            supprimer_evenement(
                evenement["id"]
            )

        except Exception as e:

            print("Erreur Google Agenda :", e)

            return "Je n'ai pas réussi à supprimer cet événement."

        titre = evenement.get(
            "summary",
            "l'événement"
        )

        return f"L'événement {titre} a été supprimé."

    elif commande == "modifier_agenda":

        recherche = extraire_titre_agenda(texte)

        if not recherche:
            return "Je n'ai pas compris quel événement modifier."

        try:

            evenements = rechercher_evenement(
                recherche,
                nombre_max=10
            )

        except Exception as e:

            print("Erreur Google Agenda :", e)

            return "Je n'ai pas réussi à consulter ton agenda."

        if not evenements:
            return (
                f"Je n'ai pas trouvé d'événement correspondant à {recherche}."
            )

        if len(evenements) > 1:
            phrases = [
                f"{i + 1}. {formater_evenement(e)}"
                for i, e in enumerate(evenements)
            ]

            return (
                "J'ai trouvé plusieurs événements : "
                + " ; ".join(phrases)
                + ". Précise lequel modifier."
            )

        evenement = evenements[0]

        nouvelle_date = extraire_date_agenda(texte)
        nouvelle_heure = extraire_heure_agenda(texte)

        if nouvelle_heure is None:
            return "Je n'ai pas compris la nouvelle heure."

        h, m = nouvelle_heure

        titre_actuel = evenement.get(
            "summary",
            "l'événement"
        )

        try:

            modifier_evenement(
                event_id=evenement["id"],
                date=nouvelle_date,
                heure_debut=f"{h:02d}:{m:02d}"
            )

        except Exception as e:

            print("Erreur Google Agenda :", e)

            return "Je n'ai pas réussi à modifier cet événement."

        return (
            f"{titre_actuel} a été déplacé au "
            f"{datetime.strptime(nouvelle_date, '%Y-%m-%d').strftime('%d/%m/%Y')} "
            f"à {h:02d} heures {m:02d}."
        )

    elif commande == "blague":
        return divertissement("blague")

    elif commande == "anecdote":
        return divertissement("anecdote")

    elif commande == "devinette":
        return divertissement("devinette")

    elif commande == "pile_ou_face":
        resultat = pile_ou_face()

        if resultat == "pile":
            return "Pile !"
        else:
            return "Face !"


    elif commande == "lancer_de":
        faces = extraire_faces_de(texte)

        try:
            resultat = lancer_de(faces)
            return f"J'ai lancé un dé à {faces} faces : {resultat} !"
        except ValueError:
            return "Un dé doit avoir au moins 2 faces."

    elif commande == "nombre_aleatoire":
        minimum, maximum = extraire_bornes_hasard(texte)

        resultat = nombre_aleatoire(minimum, maximum)

        return f"Le nombre choisi au hasard entre {minimum} et {maximum} est {resultat}."

    elif commande == "choix_aleatoire":
        choix = extraire_choix_hasard(texte)

        if not choix:
            return "Il me faut plusieurs choix entre lesquels choisir."

        resultat = choix_aleatoire(choix)

        return f"Je choisis : {resultat} !"

    elif commande == "creer_note":
        return traiter_creer_note(texte)

    elif commande == "ajouter_note":
        return traiter_ajouter_note(texte)

    elif commande == "lire_note":
        return traiter_lire_note(texte)

    elif commande == "modifier_note":
        return traiter_modifier_note(texte)

    elif commande == "supprimer_note":
        return traiter_supprimer_note(texte)

    elif commande == "vider_note":
        return traiter_vider_note(texte)

    elif commande == "renommer_note":
        return traiter_renommer_note(texte)

    elif commande == "lister_notes":
        return traiter_lister_notes()

    elif commande == "rechercher_notes":
        return traiter_rechercher_notes(texte)

    elif commande == "resumer_document":
        texte = extraire_texte_resume(texte)
        resume = resumer_avec_groq(texte)
        return f"Voici le résumé: {resume}"

    elif commande == "corriger_texte":
        texte_a_corriger = extraire_texte_correction(texte_original)

        if not texte_a_corriger:
            return "Je n'ai pas compris quel texte tu veux corriger."

        return corriger_texte(texte_a_corriger)
    
    elif commande == "au_revoir":
        return "Au revoir."

    reponse = executer(texte)

    if reponse:
        return reponse

    return "Je n'ai pas compris."