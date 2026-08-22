import re
import unicodedata
from rapidfuzz import fuzz, process
from villes import VILLES


# =========================================================
# NORMALISATION
# =========================================================

def _normaliser(texte):
    texte = str(texte).lower().strip()

    texte = unicodedata.normalize("NFD", texte)
    texte = "".join(
        c for c in texte
        if unicodedata.category(c) != "Mn"
    )

    # Uniformiser quelques séparateurs fréquents de Whisper
    texte = texte.replace("’", "'")
    texte = re.sub(r"\s+", " ", texte)

    return texte.strip()


# =========================================================
# OUTILS DE DÉTECTION
# =========================================================

def _contient_mot_entier(texte, mot):
    """
    Vérifie qu'un mot/une expression apparaît comme élément entier.

    Contrairement à:
        mot in texte

    cela évite par exemple qu'un morceau de mot déclenche
    accidentellement une commande.
    """
    mot = _normaliser(mot)

    if not mot:
        return False

    motif = r"(?<!\w)" + re.escape(mot) + r"(?!\w)"
    return re.search(motif, texte) is not None


def _contient_mot_cle(texte, mots_cles):
    return any(
        _contient_mot_entier(texte, mot)
        for mot in mots_cles
    )


def _contient_une_expression(texte, expressions):
    return any(
        _contient_mot_entier(texte, expression)
        for expression in expressions
    )


def _commence_par_une_expression(texte, expressions):
    """
    Utilisé pour les commandes qui introduisent du contenu.

    Accepte :
        "corrige ce texte Bonjour"
        "corrige ce texte : Bonjour"
        "résume ce texte Bonjour"
        "résume ce texte : Bonjour"
    """

    texte = texte.strip()

    for expression in expressions:
        expression = _normaliser(expression)

        if texte == expression:
            return True

        if texte.startswith(expression + " "):
            return True

        if texte.startswith(expression + ":"):
            return True

        if texte.startswith(expression + " :"):
            return True

    return False

# =========================================================
# EXTRAIRE UNE URL
# =========================================================

def extraire_url(texte):
    """
    Extrait la première URL présente dans une commande.

    Exemple :
        "ajoute cette brocante à mon agenda https://exemple.fr/event"

    retourne :
        "https://exemple.fr/event"
    """

    if not texte:
        return None

    match = re.search(
        r'https?://[^\s<>"\']+',
        texte
    )

    if not match:
        return None

    url = match.group(0).rstrip(".,;:!?)]}")

    return url


# =========================================================
# ACTIVATION / DÉSACTIVATION
# =========================================================

MOTIFS_DESACTIVATION = [
    "desactiv",
    "des activ",
    "dez activ"
]

MOTIFS_ACTIVATION = [
    "activ",
    "deskbot",
    "desk bot",
    "disc bot"
]


def _est_desactivation(texte):
    return any(motif in texte for motif in MOTIFS_DESACTIVATION)


def _est_activation(texte):
    return any(motif in texte for motif in MOTIFS_ACTIVATION)


# =========================================================
# AU REVOIR
# =========================================================

MOTIFS_AU_REVOIR = [
    "revoir",
    "bientot",
    "bye",
    "ciao"
]


def _est_au_revoir(texte):
    return any(
        _contient_mot_entier(texte, motif)
        for motif in MOTIFS_AU_REVOIR
    )


# =========================================================
# COMMANDES SIMPLES
# =========================================================

COMMANDES = {

    "youtube": [
        "youtube",
        "you tube",
        "you toube",
        "utube",
        "youtube."
    ],

    "google": [
        "google",
        "gougelle",
        "gouguel",
        "gogole",
        "gougueule",
        "gougel"
    ],

    "bonjour": [
        "bonjour",
        "hello",
        "bonsoir"
    ],

    "merci": [
        "merci",
        "merci beaucoup",
        "je te remercie",
        "merci deskbot",
        "merci beaucoup deskbot"
    ],

    "ça_va": [
        "ça va",
        "comment ça va",
        "comment vas-tu",
        "comment vas tu",
        "comment allez-vous",
        "comment allez vous"
    ],

    "qui_es_tu": [
        "qui es-tu",
        "qui es tu",
        "tu es quoi",
        "tu es qui",
        "qui es tu deskbot"
    ],

    "heure": [
        "quelle heure est-il",
        "quelle heure est il",
        "quelle heure est-il deskbot",
        "donne moi l'heure"
    ]

}


# =========================================================
# CHRONOMÈTRE
# =========================================================

MOTS_CLES_CHRONOMETRE = [
    "chronometre",
    "chrono"
]

COMMANDES_CHRONOMETRE = {

    "demarrer_chronometre": [
        "démarre le chronomètre",
        "lance le chronomètre",
        "démarre le chronomètre deskbot"
    ],

    "pause_chronometre": [
        "pause le chronomètre",
        "mets en pause le chronomètre",
        "pause le chronomètre deskbot"
    ],

    "temps_chronometre": [
        "affiche le chronomètre",
        "depuis quand le chronomètre est-il lancé"
    ],

    "reprendre_chronometre": [
        "reprend le chronomètre",
        "reprends le chronomètre",
        "reprend le chronomètre deskbot"
    ],

    "arreter_chronometre": [
        "arrête le chronomètre",
        "arrête le chronomètre deskbot",
        "stop le chronomètre"
    ],

    "reinitialiser_chronometre": [
        "remets le chronomètre à zéro",
        "remets le chronomètre à zéro deskbot",
        "remets le chronomètre à zéro s'il te plaît"
    ]

}


# =========================================================
# MINUTEUR / ALARMES
# =========================================================

MOTS_CLES_MINUTEUR = ["minuteur"]
MOTS_PAUSE = ["pause", "mets en pause"]
MOTS_REPRISE = ["reprend", "reprends", "continue"]
MOTS_CLES_ALARME = ["alarme"]
MOTS_TEMPS_RESTANT = ["reste", "restant", "combien de temps"]
MOTS_ALLUMER_ALARME = ["allume"]
MOTS_ETEINDRE_ALARME = ["eteins", "coupe"]
MOTS_SONNERIE = ["sonnerie"]

MOTS_ARRET = ["arrete", "stop", "annule", "supprime"]


# =========================================================
# MÉTÉO
# =========================================================

MOTS_CLES_METEO = [
    "meteo",
    "meto",
    "mettau",
    "metezo",
    "mettezvous",
    "mettezle",
    "metteu",
    "meteuo"
]


# =========================================================
# MÉTÉO - VILLES
# =========================================================

ALIAS_VILLES = {

    "fontvieille": [
        "fontvieille",
        "fouvierre",
        "afovieille",
        "fousseille",
        "fovieille",
        "fonds aie",
        "fond bien",
        "feu vieille"
    ],

    "saintes-maries-de-la-mer": [
        "saintes maries de la mer",
        "saintes-maries-de-la-mer",
        "centremarie de la mer",
        "seau de marie de la mer"
    ],

    "etable-sur-mer": [
        "etablesurmer",
        "etableu",
        "atable sur meur",
        "etablir le sommet",
        "etabre son mer",
        "etable sur mer",
        "etable sur maire"
    ],

    "hébécourt": [
        "hebecourt",
        "ebecois",
        "lhebecois",
        "hebit cours",
        "ebicant",
        "elecure"
    ],

    "gisors": [
        "jiseur",
        "jusol",
        "gisors"
    ],

    "binic": [
        "binic",
        "abonnique",
        "abinnique",
        "banic"
    ],

    "montreuil": [
        "montreuil",
        "motroil",
        "montroeil"
    ]

}


def _ville_par_alias(texte):
    for ville, alias in ALIAS_VILLES.items():
        if _contient_une_expression(texte, alias):
            return ville

    return None


def _ville_apres_a(texte, seuil=70):
    mots = texte.split()

    for i, mot in enumerate(mots):

        if mot == "a":

            reste = " ".join(mots[i + 1:])

            if not reste:
                continue

            resultat = process.extractOne(
                reste,
                VILLES,
                scorer=fuzz.ratio,
                score_cutoff=seuil
            )

            if resultat:
                return resultat[0]

    return None


# =========================================================
# MUSIQUE
# =========================================================

MUSIQUES_CONNUES = [
    "lofi relax",
    "lofi pour coder",
    "lofi pour travailler",
    "lofi pour dormir",
    "lofi pour se concentrer",
    "lofi gaming"
]

COMMANDES_MUSIQUE = {

    "stop_musique": [
        "arrête la musique",
        "stop la musique",
        "coupe la musique"
    ],

    "pause_musique": [
        "pause la musique",
        "mets en pause"
    ],

    "musique": [
        "joue de la musique",
        "lance de la musique",
        "mets de la musique",
        "écoute de la musique",
        "joue un morceau",
        "joue",
        "lance",
        "écoute"
    ]

}

MOTS_CLES_VOLUME = ["volume"]
MOTS_AUGMENTER_VOLUME = ["monte", "augmente", "plus fort", "plus haut"]
MOTS_DIMINUER_VOLUME = ["baisse", "diminue", "moins fort", "moins haut"]


# =========================================================
# MAILS
# =========================================================

MOTS_CLES_MAIL = ["mail", "mails", "email", "emails", "courriel"]


# =========================================================
# RECHERCHE
# =========================================================

MOTS_CLES_GOOGLE_RECHERCHE = ["google"]
MOTS_RECHERCHE = ["recherche", "cherche"]


# =========================================================
# STATS YOUTUBE
# =========================================================

MOTS_CLES_STATS_YOUTUBE = ["statistique", "statistiques", "stats"]


# =========================================================
# TRAJETS
# =========================================================

MOTS_CLES_TRAJET = ["trajet", "itineraire", "itinéraire"]


# =========================================================
# PRONOTE
# =========================================================

MOTS_CLES_PRONOTE = ["pronote"]
MOTS_EMPLOI_DU_TEMPS = ["emploi du temps", "cours"]
MOTS_DEVOIRS = ["devoir", "devoirs"]
MOTS_NOTES = ["note", "notes", "moyenne"]
MOTS_ABSENTS = ["absent", "absents"]


# =========================================================
# TO-DO LIST
# =========================================================

MOTS_CLES_TODO = [
    "todo",
    "to do",
    "tache",
    "taches",
    "liste de taches",
    "liste des taches"
]

MOTS_AJOUT_TODO = [
    "ajoute",
    "ajouter",
    "rajoute",
    "rajouter",
    "mets"
]

MOTS_AFFICHER_TODO = [
    "affiche",
    "montre",
    "voir",
    "consulte",
    "qu'est-ce qu'il y a",
    "quest ce qu'il y a"
]

MOTS_TERMINER_TODO = [
    "termine",
    "terminer",
    "terminee",
    "fini",
    "finie",
    "fait",
    "faite"
]

MOTS_ANNULE_TODO = [
    "annule",
    "remets",
    "annuler",
    "remettre"
]

MOTS_SUPPRIMER_TODO = [
    "supprime",
    "supprimer",
    "enleve",
    "enlever",
    "retire",
    "retirer"
]

MOTS_VIDER_TODO = [
    "vide",
    "vider",
    "efface tout",
    "supprime tout"
]

MOTS_SUPPRIMER_TACHES_TERMINEES = [
    "supprime les taches terminees",
    "supprimer les taches terminees",
    "efface les taches terminees",
    "effacer les taches terminees",
    "enleve les taches terminees",
    "enlever les taches terminees"
]


# =========================================================
# DEMANDER À L'IA
# =========================================================

MOTS_QUESTIONS_IA = [
    "demande",
    "ia",
    "intelligence artificielle",
    "est-ce-que",
    "pose une question",
    "question",
    "demande à l'ia"
]


# =========================================================
# SESSION DE RÉVISION
# =========================================================

MOTS_SESSION_REVISION = [
    "session de revision",
    "révision",
    "session",
    "pomodoro",
    "travail",
    "travailler"
]


# =========================================================
# RÉPÉTER
# =========================================================

MOTS_CLES_REPETER = [
    "répète",
    "repete",
    "répeter",
    "répète après-moi",
    "répète ce que je dis"
]


# =========================================================
# CALCULER
# =========================================================

# Les opérateurs seuls ne déclenchent plus la commande.
# Ils sont utilisés uniquement en présence d'un vrai signal
# de calcul.
MOTS_CLES_CALCULER = [
    "calcule",
    "calcul",
    "fais le calcul",
    "combien font",
    "combien fait",
    "effectue le calcul"
]

MOTS_OPERATEURS_CALCUL = [
    "fois",
    "divise",
    "divisé",
    "moins",
    "plus",
    "multiplié",
    "additionne",
    "soustrait"
]


# =========================================================
# CONVERTIR
# =========================================================

# Les monnaies seules ne déclenchent plus "convertir".
# Elles doivent être accompagnées d'un verbe / signal de conversion.
MOTS_CLES_CONVERTIR = [
    "convertis",
    "convertir",
    "conversion",
    "convertit",
    "converti",
    "fais une conversion",
    "convertis moi"
]

MOTS_UNITES_CONVERSION = [
    "euro",
    "euros",
    "dollar",
    "dollars",
    "yen",
    "livre",
    "livres"
]


# =========================================================
# TRADUCTION
# =========================================================

# IMPORTANT :
# Les langues seules ne déclenchent plus "traduire".
# "traduction" dans un texte à résumer ne déclenche donc
# plus la traduction.
MOTS_CLES_TRADUCTION = [
    "traduis",
    "traduire",
    "traduction",
    "traduit",
    "traduis moi",
    "traduis-moi"
]

MOTS_LANGUES = [
    "francais",
    "anglais",
    "italien",
    "espagnol",
    "allemand"
]

# Formulations fortes qui indiquent clairement une traduction
PHRASES_TRADUCTION = [
    "traduis ce texte",
    "traduis le texte",
    "traduis cette phrase",
    "traduis la phrase",
    "traduis moi ce texte",
    "traduis-moi ce texte",
    "traduire ce texte",
    "traduire le texte",
    "fais une traduction",
    "fais moi une traduction",
    "fais-moi une traduction"
]


# =========================================================
# NOTIFICATION
# =========================================================

MOTS_CLES_NOTIFICATION = [
    "programme",
    "creer",
    "programmer",
    "cree",
    "notif",
    "notification"
]


# =========================================================
# VÉRIFICATION JOURNALIÈRE
# =========================================================

MOTS_CLES_VERIFICATION_JOURNALIERE = [
    "verification journaliere",
    "verification quotidienne",
    "verification",
    "fais le point",
    "le point",
    "verif"
]


# =========================================================
# GOOGLE AGENDA
# =========================================================

MOTS_CLES_AGENDA = [
    "agenda",
    "calendrier",
    "evenement",
    "evenements",
    "rendez-vous",
    "rendez vous",
    "rdv"
]

MOTS_AJOUT_AGENDA = [
    "ajoute",
    "ajouter",
    "cree",
    "creer",
    "programme",
    "programmer",
    "planifie",
    "planifier",
    "mets"
]

MOTS_AFFICHER_AGENDA = [
    "affiche",
    "montre",
    "voir",
    "consulte",
    "regarde",
    "qu'est-ce qu'il y a",
    "quest ce qu'il y a",
    "qu'est ce que j'ai",
    "quest ce que j'ai",
    "ce que j'ai"
]

MOTS_PROCHAINS_AGENDA = [
    "prochain",
    "prochains",
    "prochaine",
    "prochaines"
]

MOTS_SUPPRIMER_AGENDA = [
    "supprime",
    "supprimer",
    "enleve",
    "enlever",
    "retire",
    "retirer",
    "annule",
    "annuler"
]

MOTS_MODIFIER_AGENDA = [
    "modifie",
    "modifier",
    "change",
    "changer",
    "decale",
    "déplace",
    "deplace",
    "déplacer",
    "deplacer"
]

MOTS_CLES_AGENDA_URL = [
    "ajoute cette brocante",
    "ajouter cette brocante",
    "mets cette brocante",
    "mettre cette brocante",
    "ajoute cet evenement",
    "ajouter cet evenement",
    "mets cet evenement",
    "mettre cet evenement",
    "ajoute cet événement",
    "ajouter cet événement",
    "mets cet événement",
    "mettre cet événement",
    "ajoute ce rendez vous",
    "ajouter ce rendez vous",
    "mets ce rendez vous",
    "mettre ce rendez vous",
    "ajoute ce rdv",
    "ajouter ce rdv",
    "mets ce rdv",
    "mettre ce rdv"
]


# =========================================================
# BLAGUES
# =========================================================

MOTS_CLES_BLAGUES = [
    "blague",
    "blagues",
    "raconte moi une blage",
    "fais moi une blague",
    "rire",
    "rigoler"
]


# =========================================================
# ANECDOTES
# =========================================================

MOTS_CLES_ANECDOTES = [
    "anecdote",
    "anecdotes",
    "raconte une anecdote",
    "dis une anecdote",
    "apprendre",
    "savoir"
]


# =========================================================
# DEVINETTES
# =========================================================

MOTS_CLES_DEVINETTES = [
    "devinette",
    "devinettes",
    "pose moi une devinette",
    "fais moi une devinette"
]


# =========================================================
# PILE OU FACE
# =========================================================

MOTS_CLES_PILE_OU_FACE = [
    "pile ou face",
    "pile face",
    "pile ou pile"
]


# =========================================================
# LANCER DE DÉ
# =========================================================

MOTS_CLES_LANCER_DE = [
    "lance un dé",
    "lancer un dé",
    "lance le dé",
    "lancer le dé",
    "jette un dé",
    "jeter un dé",
    "lance un d",
    "lancer un d"
]


# =========================================================
# NOMBRE ALÉATOIRE
# =========================================================

MOTS_CLES_NOMBRE_ALEATOIRE = [
    "nombre aléatoire",
    "nombre au hasard",
    "nombre hasard",
    "donne moi un nombre au hasard",
    "donne moi un nombre aléatoire"
]


# =========================================================
# CHOIX ALÉATOIRE
# =========================================================

MOTS_CLES_CHOIX_ALEATOIRE = [
    "choisis au hasard",
    "choisi au hasard",
    "fais un choix au hasard",
    "choix au hasard",
    "choix au aléatoire"
]


# =========================================================
# COMMANDES NOTES
# =========================================================

MOTS_CLES_CREER_NOTE = [
    "cree une note",
    "creer une note",
    "nouvelle note",
    "ajoute une note",
    "ajouter une note"
]

MOTS_CLES_AJOUTER_NOTE = [
    "ajoute",
    "ajouter",
    "rajoute",
    "rajouter",
    "complete",
    "completer"
]

MOTS_CLES_LIRE_NOTE = [
    "lis ma note",
    "lire ma note",
    "affiche ma note",
    "afficher ma note",
    "montre ma note",
    "montrer ma note"
]

MOTS_CLES_MODIFIER_NOTE = [
    "modifie ma note",
    "modifier ma note",
    "modifie le contenu de ma note",
    "modifier le contenu de ma note"
]

MOTS_CLES_SUPPRIMER_NOTE = [
    "supprime ma note",
    "supprimer ma note",
    "efface ma note",
    "effacer ma note"
]

MOTS_CLES_VIDER_NOTE = [
    "vide ma note",
    "vider ma note",
    "efface le contenu de ma note",
    "effacer le contenu de ma note"
]

MOTS_CLES_RENOMMER_NOTE = [
    "renomme ma note",
    "renommer ma note"
]

MOTS_CLES_LISTER_NOTE = [
    "liste mes notes",
    "lister mes notes",
    "affiche mes notes",
    "afficher mes notes",
    "montre mes notes",
    "quelles sont mes notes",
    "quels sont mes notes"
]

MOTS_CLES_RECHERCHER_NOTE = [
    "cherche dans mes notes",
    "chercher dans mes notes",
    "recherche dans mes notes",
    "rechercher dans mes notes"
]


# =========================================================
# RÉSUMER UN DOCUMENT
# =========================================================

# Expressions fortes placées volontairement avant la traduction.
# Elles doivent être reconnues même si le contenu contient
# les mots "traduction", "anglais", "français", etc.
MOTS_CLES_RESUMER_DOCUMENT = [
    "resume ce document",
    "resume le document",
    "resume ce texte",
    "resume le texte",
    "fais un resume de ce document",
    "fais le resume de ce document",
    "fais moi un resume de ce document",
    "fais-moi un resume de ce document",
    "fais un resume de ce texte",
    "fais moi un resume de ce texte",
    "fais-moi un resume de ce texte",
    "resume ceci",
    "resume ca"
]

PHRASES_RESUME_FORTES = MOTS_CLES_RESUMER_DOCUMENT + [
    "resume",
    "resumer",
    "fais un resume",
    "fais moi un resume",
    "fais-moi un resume"
]

#CORRIGER UN TEXTE

MOTS_CLES_CORRECTION = [
    "corrige ce texte",
    "corriger ce texte",
    "corrige le texte",
    "corriger le texte",
    "corige ce texte",
    "corige le texte",
    "corrige moi ce texte",
    "corriger moi ce texte",
    "corrige-moi ce texte",
    "corriger-moi ce texte",
]


# =========================================================
# OUTILS DE SCORING
# =========================================================

def _longueur_raisonnable(texte, phrase, facteur=4):
    n_texte = len(texte.split())
    n_phrase = len(phrase.split())

    return n_texte <= max(n_phrase * facteur, 3)


def _meilleur_score(texte, variantes):
    meilleur = 0

    for phrase in variantes:

        phrase = _normaliser(phrase)

        if not _longueur_raisonnable(texte, phrase):
            continue

        score = fuzz.WRatio(texte, phrase)

        if score > meilleur:
            meilleur = score

    return meilleur


def _meilleure_commande(texte, dictionnaire, seuil=70):
    meilleur_nom = None
    meilleur_score = 0

    for nom, variantes in dictionnaire.items():

        score = _meilleur_score(texte, variantes)

        if score > meilleur_score:
            meilleur_score = score
            meilleur_nom = nom

    if meilleur_score >= seuil:
        return meilleur_nom

    return None


def _contient_musique_connue(texte, seuil=75):
    for nom in MUSIQUES_CONNUES:
        if fuzz.partial_ratio(texte, _normaliser(nom)) >= seuil:
            return True

    return False


# =========================================================
# COMMANDES PRIORITAIRES À CONTENU
# =========================================================

def _detecter_commande_a_contenu(texte):
    """
    Détecte d'abord les commandes qui introduisent un contenu.

    C'est essentiel pour éviter les collisions du type :

        "résume ce texte : la traduction..."

    Le mot "traduction" appartient au contenu et ne doit pas
    déclencher la commande "traduire".
    """

    if _commence_par_une_expression(
        texte,
        MOTS_CLES_CORRECTION
    ):
        return "corriger_texte"

    # -----------------------------------------------------
    # RÉSUMÉ
    # -----------------------------------------------------

    if _commence_par_une_expression(
        texte,
        PHRASES_RESUME_FORTES
    ):
        return "resumer_document"

    # -----------------------------------------------------
    # TRADUCTION
    # -----------------------------------------------------

    if _commence_par_une_expression(
        texte,
        PHRASES_TRADUCTION
    ):
        return "traduire"

    # -----------------------------------------------------
    # NOTES
    # -----------------------------------------------------

    if _contient_une_expression(
        texte,
        MOTS_CLES_CREER_NOTE
    ):
        return "creer_note"

    if (
        _contient_mot_cle(
            texte,
            ["a ma note", "a la note", "dans ma note", "dans la note"]
        )
        and _contient_mot_cle(
            texte,
            MOTS_CLES_AJOUTER_NOTE
        )
    ):
        return "ajouter_note"

    return None


# =========================================================
# FONCTION PRINCIPALE
# =========================================================

def trouver_commande(texte):

    if texte is None:
        return None

    texte = _normaliser(texte)

    if not texte:
        return None

    # =====================================================
    # 0. COMMANDES QUI INTRODUISENT DU CONTENU
    # =====================================================
    #
    # PRIORITÉ MAXIMALE.
    #
    # Exemple :
    # "résume ce texte la traduction a été inventée en 1956"
    #
    # => resumer_document
    #
    # et non traduire.
    #
    commande = _detecter_commande_a_contenu(texte)

    if commande:
        return commande

    # =====================================================
    # 1. ACTIVATION / DÉSACTIVATION
    # =====================================================

    if _est_desactivation(texte):
        return "desactivation"

    if _est_activation(texte):
        return "activation"

    # =====================================================
    # 2. AU REVOIR
    # =====================================================

    if _est_au_revoir(texte):
        return "au_revoir"

    # =====================================================
    # 3. CHRONOMÈTRE
    # =====================================================

    if _contient_mot_cle(texte, MOTS_CLES_CHRONOMETRE):

        commande = _meilleure_commande(
            texte,
            COMMANDES_CHRONOMETRE,
            seuil=60
        )

        if commande:
            return commande

    # =====================================================
    # 4. MINUTEUR
    # =====================================================

    if _contient_mot_cle(texte, MOTS_CLES_MINUTEUR):

        if _contient_mot_cle(texte, MOTS_TEMPS_RESTANT):
            return "temps_minuteur"

        if _contient_mot_cle(texte, MOTS_PAUSE):
            return "pause_minuteur"

        if _contient_mot_cle(texte, MOTS_REPRISE):
            return "reprendre_minuteur"

        if _contient_mot_cle(texte, MOTS_ARRET):
            return "arreter_minuteur"

        return "demarrer_minuteur"

    # =====================================================
    # 5. ALARME
    # =====================================================

    if _contient_mot_cle(texte, MOTS_CLES_ALARME):

        if (
            _contient_mot_cle(texte, MOTS_TEMPS_RESTANT)
            or _contient_mot_cle(texte, ["quand", "prochaine"])
        ):
            return "temps_alarme"

        if _contient_mot_cle(texte, MOTS_SONNERIE):
            return "sonnerie_alarme"

        if _contient_mot_cle(texte, MOTS_ALLUMER_ALARME):
            return "allumer_alarme"

        if _contient_mot_cle(texte, MOTS_ETEINDRE_ALARME):
            return "eteindre_alarme"

        if _contient_mot_cle(texte, MOTS_ARRET):
            return "supprimer_alarmes"

        return "ajouter_alarme"

    # =====================================================
    # 5,1. AGENDA DEPUIS UNE URL
    # =====================================================
    
    url = extraire_url(texte)
    
    if url:
    
        intention_ajout = _contient_mot_cle(
            texte,
            MOTS_AJOUT_AGENDA
        )
    
        concerne_agenda = _contient_mot_cle(
            texte,
            MOTS_CLES_AGENDA
        )
    
        if intention_ajout and concerne_agenda:
            return "ajouter_agenda_url"

    # =====================================================
    # 6. TRAJETS
    # =====================================================

    if _contient_mot_cle(texte, MOTS_CLES_TRAJET):
        return "calculer_trajet"

    # =====================================================
    # 7. MÉTÉO
    # =====================================================

    if _contient_mot_cle(texte, MOTS_CLES_METEO):
        return "meteo"

    if _ville_par_alias(texte):
        return "meteo"

    if _ville_apres_a(texte):
        return "meteo"

    # =====================================================
    # 8. MUSIQUE
    # =====================================================

    if _contient_musique_connue(texte):
        return "musique"

    if _contient_mot_cle(texte, ["musique"]):

        commande = _meilleure_commande(
            texte,
            COMMANDES_MUSIQUE,
            seuil=60
        )

        if commande:
            return commande

    # Volume : nécessite le mot "volume"
    if _contient_mot_cle(texte, MOTS_CLES_VOLUME):

        if _contient_mot_cle(texte, MOTS_AUGMENTER_VOLUME):
            return "augmenter_volume"

        if _contient_mot_cle(texte, MOTS_DIMINUER_VOLUME):
            return "diminuer_volume"

        return "regler_volume"

    # =====================================================
    # 9. MAILS
    # =====================================================

    if _contient_mot_cle(texte, MOTS_CLES_MAIL):
        return "verifier_mails"

    # =====================================================
    # 10. RECHERCHE GOOGLE
    # =====================================================

    if (
        _contient_mot_cle(texte, MOTS_CLES_GOOGLE_RECHERCHE)
        and _contient_mot_cle(texte, MOTS_RECHERCHE)
    ):

        if _contient_mot_cle(texte, ["resultat", "résultat"]):
            return "recherche_resultat"

        return "recherche_paragraphe"

    # =====================================================
    # 11. STATS YOUTUBE
    # =====================================================

    if (
        _contient_mot_cle(texte, ["youtube"])
        and _contient_mot_cle(texte, MOTS_CLES_STATS_YOUTUBE)
    ):
        return "stats_youtube"

    # =====================================================
    # 12. PRONOTE
    # =====================================================

    if _contient_mot_cle(texte, MOTS_CLES_PRONOTE):

        if _contient_mot_cle(texte, MOTS_ABSENTS):
            return "pronote_absents"

        if _contient_mot_cle(texte, MOTS_NOTES):
            return "pronote_notes"

        if _contient_mot_cle(texte, MOTS_DEVOIRS):
            return "pronote_devoirs"

        if _contient_mot_cle(texte, MOTS_EMPLOI_DU_TEMPS):
            return "pronote_emploi_du_temps"

    # =====================================================
    # 13. TO-DO
    # =====================================================

    if (
        _contient_mot_cle(texte, MOTS_AJOUT_TODO)
        and '"' in texte
    ):
        return "ajouter_todo"

    if _contient_mot_cle(texte, MOTS_CLES_TODO):

        if _contient_mot_cle(texte, MOTS_VIDER_TODO):
            return "vider_todo"

        if (
            _contient_mot_cle(texte, MOTS_SUPPRIMER_TODO)
            and _contient_mot_cle(
                texte,
                ["termine", "terminee", "terminees"]
            )
        ):
            return "supprimer_taches_terminees"

        if _contient_mot_cle(texte, MOTS_TERMINER_TODO):
            return "terminer_todo"

        if _contient_mot_cle(texte, MOTS_ANNULE_TODO):
            return "annule_todo"

        if _contient_mot_cle(texte, MOTS_SUPPRIMER_TODO):
            return "supprimer_todo"

        if _contient_mot_cle(texte, MOTS_AJOUT_TODO):
            return "ajouter_todo"

        if _contient_mot_cle(texte, MOTS_AFFICHER_TODO):
            return "afficher_todo"

        return "afficher_todo"

    # =====================================================
    # 14. QUESTION IA
    # =====================================================

    # "question" seul n'est plus suffisant.
    # On exige un signal IA explicite ou une formulation claire.
    if _contient_mot_cle(
        texte,
        [
            "ia",
            "intelligence artificielle",
            "demande a l ia",
            "demande a ia"
        ]
    ):
        return "question_ia"

    if _contient_mot_cle(
        texte,
        ["pose une question"]
    ):
        return "question_ia"

    # =====================================================
    # 15. SESSION DE RÉVISION
    # =====================================================

    if _contient_mot_cle(texte, MOTS_SESSION_REVISION):
        return "session_revision"

    # =====================================================
    # 16. RÉPÉTER
    # =====================================================

    if _contient_mot_cle(texte, MOTS_CLES_REPETER):
        return "repeter"

    # =====================================================
    # 17. CALCUL
    # =====================================================

    # Un opérateur seul ("plus", "moins", "fois") ne déclenche
    # plus la calculatrice.
    if _contient_mot_cle(texte, MOTS_CLES_CALCULER):
        return "calculer"

    # Si Whisper a raté "calcule", on accepte une expression
    # mathématique évidente avec chiffres + opérateur.
    contient_nombre = bool(re.search(r"\d", texte))

    if (
        contient_nombre
        and _contient_mot_cle(texte, MOTS_OPERATEURS_CALCUL)
    ):
        return "calculer"

    # =====================================================
    # 18. CONVERSION
    # =====================================================

    # Les mots "euro", "dollar", etc. seuls ne suffisent plus.
    # Il faut un véritable signal de conversion.
    if _contient_mot_cle(texte, MOTS_CLES_CONVERTIR):
        return "convertir"

    # Filet de sécurité pour :
    # "combien font 10 euros en dollars"
    if (
        _contient_mot_cle(texte, ["en"])
        and _contient_mot_cle(texte, MOTS_UNITES_CONVERSION)
    ):
        nombre = bool(re.search(r"\d", texte))

        if nombre:
            return "convertir"

    # =====================================================
    # 19. TRADUCTION
    # =====================================================

    # IMPORTANT :
    # On ne déclenche PAS la traduction uniquement parce qu'un
    # texte contient "traduction", "anglais", "français", etc.
    #
    # Les formulations fortes ont déjà été traitées tout en haut.
    #
    # Ici, on accepte encore :
    # "traduis en anglais"
    # "traduire en anglais"
    # etc.
    if _contient_mot_cle(
        texte,
        ["traduis", "traduire", "traduit", "traduis moi", "traduis-moi"]
    ):
        return "traduire"

    # =====================================================
    # 20. NOTIFICATION
    # =====================================================

    if _contient_mot_cle(
        texte,
        [
            "notification",
            "notif"
        ]
    ):
        return "notification"

    # "programme" / "programmer" sont trop génériques seuls.
    # On les accepte seulement avec un indice temporel ou notif.
    if (
        _contient_mot_cle(
            texte,
            ["programme", "programmer", "programmer"]
        )
        and _contient_mot_cle(
            texte,
            [
                "dans",
                "a",
                "à",
                "demain",
                "ce soir",
                "heure",
                "minutes",
                "minute"
            ]
        )
    ):
        return "notification"

    # =====================================================
    # 21. VÉRIFICATION JOURNALIÈRE
    # =====================================================

    if _contient_mot_cle(
        texte,
        MOTS_CLES_VERIFICATION_JOURNALIERE
    ):
        return "verification_journaliere"

    # =====================================================
    # 22. GOOGLE AGENDA
    # =====================================================

    if _contient_mot_cle(texte, MOTS_CLES_AGENDA):

        if _contient_mot_cle(texte, MOTS_MODIFIER_AGENDA):
            return "modifier_agenda"

        if _contient_mot_cle(texte, MOTS_SUPPRIMER_AGENDA):
            return "supprimer_agenda"

        if _contient_mot_cle(texte, MOTS_AJOUT_AGENDA):
            return "ajouter_agenda"

        if _contient_mot_cle(texte, MOTS_PROCHAINS_AGENDA):
            return "prochains_agenda"

        if _contient_mot_cle(texte, MOTS_AFFICHER_AGENDA):
            return "afficher_agenda"

        return "afficher_agenda"

    # =====================================================
    # 23. AGENDA SANS MOT "AGENDA"
    # =====================================================

    if _contient_mot_cle(
        texte,
        ["rendez-vous", "rendez vous", "rdv", "evenement", "evenements"]
    ):

        if _contient_mot_cle(texte, MOTS_MODIFIER_AGENDA):
            return "modifier_agenda"

        if _contient_mot_cle(texte, MOTS_SUPPRIMER_AGENDA):
            return "supprimer_agenda"

        if _contient_mot_cle(texte, MOTS_AJOUT_AGENDA):
            return "ajouter_agenda"

        return "afficher_agenda"

    # =====================================================
    # 24. BLAGUE
    # =====================================================

    if _contient_mot_cle(texte, MOTS_CLES_BLAGUES):
        return "blague"

    # =====================================================
    # 25. ANECDOTE
    # =====================================================

    if _contient_mot_cle(texte, MOTS_CLES_ANECDOTES):
        return "anecdote"

    # =====================================================
    # 26. DEVINETTE
    # =====================================================

    if _contient_mot_cle(texte, MOTS_CLES_DEVINETTES):
        return "devinette"

    # =====================================================
    # 27. PILE OU FACE
    # =====================================================

    if _contient_mot_cle(texte, MOTS_CLES_PILE_OU_FACE):
        return "pile_ou_face"

    # =====================================================
    # 28. LANCER DE DÉ
    # =====================================================

    if _contient_mot_cle(texte, MOTS_CLES_LANCER_DE):
        return "lancer_de"

    # =====================================================
    # 29. NOMBRE ALÉATOIRE
    # =====================================================

    if _contient_mot_cle(texte, MOTS_CLES_NOMBRE_ALEATOIRE):
        return "nombre_aleatoire"

    # =====================================================
    # 30. CHOIX ALÉATOIRE
    # =====================================================

    if _contient_mot_cle(texte, MOTS_CLES_CHOIX_ALEATOIRE):
        return "choix_aleatoire"

    # =====================================================
    # 31. NOTES
    # =====================================================

    if (
        _contient_mot_cle(
            texte,
            ["a ma note", "a la note", "dans ma note", "dans la note"]
        )
        and _contient_mot_cle(
            texte,
            MOTS_CLES_AJOUTER_NOTE
        )
    ):
        return "ajouter_note"

    if _contient_mot_cle(texte, MOTS_CLES_CREER_NOTE):
        return "creer_note"

    if (
        _contient_mot_cle(texte, MOTS_CLES_AJOUTER_NOTE)
        and _contient_mot_cle(
            texte,
            ["note", "ma note", "la note"]
        )
    ):
        return "ajouter_note"

    if _contient_mot_cle(texte, MOTS_CLES_LIRE_NOTE):
        return "lire_note"

    if _contient_mot_cle(texte, MOTS_CLES_MODIFIER_NOTE):
        return "modifier_note"

    if _contient_mot_cle(texte, MOTS_CLES_SUPPRIMER_NOTE):
        return "supprimer_note"

    if _contient_mot_cle(texte, MOTS_CLES_VIDER_NOTE):
        return "vider_note"

    if _contient_mot_cle(texte, MOTS_CLES_RENOMMER_NOTE):
        return "renommer_note"

    if _contient_mot_cle(texte, MOTS_CLES_LISTER_NOTE):
        return "lister_notes"

    if _contient_mot_cle(texte, MOTS_CLES_RECHERCHER_NOTE):
        return "rechercher_notes"

    # =====================================================
    # COMMANDES SIMPLES CLASSIQUES
    # =====================================================

    commande = _meilleure_commande(texte, COMMANDES)

    if commande:
        return commande

    # =====================================================
    # DERNIER RECOURS : MUSIQUE
    # =====================================================

    commande = _meilleure_commande(
        texte,
        {"musique": COMMANDES_MUSIQUE["musique"]},
        seuil=85
    )

    if commande:
        return commande

    return None


# =========================================================
# TEST RAPIDE
# =========================================================
#
# Tu peux lancer ce fichier directement pour vérifier les
# principales collisions.
#
# python commandes.py
# =========================================================

if __name__ == "__main__":

    tests = [
        "résume ce texte : la traduction a été inventée en 1956",
        "résume ce document qui parle d'anglais",
        "traduis ce texte en anglais",
        "traduire cette phrase en français",
        "ce texte parle de traduction",
        "calcule 25 plus 17",
        "résume ce texte qui contient le mot plus",
        "combien font 25 fois 4",
        "parle-moi de l'euro",
        "convertis 50 euros en dollars",
        "lance le chronomètre",
        "lance de la musique",
        "quelle heure est-il"
    ]

    print("\n===== TEST RECONNAISSANCE DES COMMANDES =====\n")

    for phrase in tests:
        resultat = trouver_commande(phrase)
        print(f"{phrase}")
        print(f"  -> {resultat}\n")