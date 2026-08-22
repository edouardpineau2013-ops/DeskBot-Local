import random
import re
import unicodedata


BLAGUES = [
    "Pourquoi les plongeurs plongent-ils toujours en arrière ? Parce que sinon ils tombent dans le bateau.",
    "Quel est le comble pour un électricien ? De ne pas être au courant.",
    "Pourquoi les ordinateurs ont-ils froid ? Parce qu'ils laissent leurs fenêtres ouvertes.",
    "Que dit un zéro à un huit ? Belle ceinture !",
    "Quel est le fruit préféré des poissons ? La pêche.",
    "Pourquoi le livre de maths est-il triste ? Parce qu'il a trop de problèmes.",
    "Quel est le comble pour un jardinier ? Se planter.",
    "Quel est le comble pour un serrurier ? Se faire mettre à la porte.",
    "Quel est le comble pour un boulanger ? Se faire rouler dans la farine.",
    "Quel est le comble pour un facteur ? Perdre l'adresse.",
    "Quel est le comble pour un photographe ? Manquer de recul.",
    "Quel est le comble pour un musicien ? Perdre la clé.",
    "Quel est le comble pour un professeur de géographie ? Perdre le nord.",
    "Quel est le comble pour un dentiste ? Avoir une dent contre quelqu'un.",
    "Quel est le comble pour un menuisier ? Prendre la porte.",
    "Pourquoi les squelettes ne se battent-ils jamais ? Parce qu'ils n'ont pas les tripes.",
    "Pourquoi les fantômes sont-ils de mauvais menteurs ? Parce qu'on voit à travers eux.",
    "Pourquoi les livres ont-ils toujours froid ? Parce qu'ils ont une couverture.",
    "Pourquoi les tomates rougissent-elles ? Parce qu'elles voient la salade se faire déshabiller.",
    "Pourquoi les escargots n'aiment-ils pas déménager ? Parce qu'ils ont déjà leur maison sur le dos.",
    "Pourquoi les ordinateurs vont-ils chez le médecin ? Parce qu'ils ont attrapé un virus.",
    "Pourquoi les développeurs aiment-ils le café ? Parce que sans café, ils ont des bugs.",
    "Quel est le plat préféré des informaticiens ? Les cookies.",
    "Pourquoi les informaticiens confondent-ils Halloween et Noël ? Parce que OCT 31 = DEC 25.",
    "Pourquoi le programmeur est-il allé à la plage ? Pour chercher des bugs.",
    "Pourquoi les développeurs détestent-ils la nature ? Parce qu'il y a trop de bugs.",
    "Que dit un ordinateur quand il a faim ? J'ai besoin d'un byte.",
    "Pourquoi le disque dur est-il mauvais en danse ? Parce qu'il manque de fluidité.",
    "Quel est le comble pour un ordinateur ? Avoir une souris qui lui fait peur.",
    "Pourquoi le calendrier est-il stressé ? Parce que ses jours sont comptés.",
    "Pourquoi l'horloge a-t-elle été renvoyée ? Parce qu'elle prenait trop de retard.",
    "Quel est le comble pour une montre ? Perdre du temps.",
    "Pourquoi les chaussures sont-elles de bonnes amies ? Parce qu'elles restent toujours à tes pieds.",
    "Pourquoi les chaussettes sont-elles toujours séparées ? Parce qu'elles ont du mal à garder la paire.",
    "Pourquoi les lunettes sont-elles populaires ? Parce qu'elles ont beaucoup de points de vue.",
    "Pourquoi la chaise est-elle fatiguée ? Parce qu'elle porte tout le monde.",
    "Pourquoi la porte est-elle si polie ? Parce qu'elle laisse toujours passer les autres.",
    "Pourquoi le frigo est-il calme ? Parce qu'il garde toujours son sang-froid.",
    "Pourquoi les œufs ne racontent-ils jamais de secrets ? Parce qu'ils risquent de se faire casser.",
    "Pourquoi les bananes mettent-elles de la crème solaire ? Parce qu'elles ont peur de peler.",
    "Quel est le fruit le plus ponctuel ? La datte.",
    "Quel est le fruit le plus sportif ? La pêche, parce qu'elle a toujours la pêche.",
    "Pourquoi le raisin ne répond-il jamais au téléphone ? Parce qu'il est pressé.",
    "Pourquoi le pain est-il toujours détendu ? Parce qu'il a déjà pris la mie.",
    "Pourquoi le fromage ne raconte-t-il pas de secrets ? Parce qu'il est trop coulant.",
    "Pourquoi le vent est-il difficile à attraper ? Parce qu'il file toujours.",
    "Pourquoi les étoiles sont-elles mauvaises en cache-cache ? Parce qu'elles brillent toujours.",
    "Pourquoi le soleil ne se dispute-t-il jamais ? Parce qu'il préfère rester positif.",
    "Pourquoi le volcan est-il énervé ? Parce qu'il a tout gardé en lui.",
    "Quel est le comble pour un pêcheur ? Se faire mener en bateau.",
    "Pourquoi les chats n'aiment-ils pas l'ordinateur ? Parce qu'ils ont peur de la souris.",
    "Pourquoi les chiens aiment-ils les ordinateurs ? Parce qu'ils peuvent poursuivre la souris.",
    "Quel est le comble pour un cheval ? Être à cheval sur les principes.",
    "Pourquoi les vaches ferment-elles les yeux quand elles donnent du lait ? Parce qu'elles veulent faire du lait concentré.",
    "Quel est le comble pour un voleur ? Voler de ses propres ailes.",
    "Quel est le comble pour un pompier ? Avoir un coup de foudre.",
    "Quel est le comble pour un pilote ? Avoir le mal de l'air.",
    "Quel est le comble pour un banquier ? Perdre le compte.",
    "Quel est le comble pour un médecin ? Être malade de rire.",
    "Quel est le comble pour un marin ? Avoir le mal de mer.",
    "Quel est le comble pour un cuisinier ? Ne pas être dans son assiette.",
    "Quel est le comble pour un opticien ? Ne pas voir plus loin que le bout de son nez.",
]


ANECDOTES = [
    "Les pieuvres ont trois cœurs.",
    "Une journée sur Vénus est plus longue qu'une année sur Vénus.",
    "Les bananes sont naturellement légèrement radioactives à cause du potassium qu'elles contiennent.",
    "Les requins existaient déjà avant les dinosaures.",
    "Le miel peut se conserver extrêmement longtemps s'il est correctement stocké.",
    "Les flamants roses doivent leur couleur aux pigments présents dans leur alimentation.",
    "La Tour Eiffel peut mesurer plusieurs centimètres de plus en été à cause de la dilatation thermique du métal.",
    "Les poulpes ont du sang bleu.",
    "Les girafes ont, comme les humains, sept vertèbres cervicales.",
    "Les koalas possèdent des empreintes digitales très proches de celles des humains.",
    "Les abeilles peuvent indiquer à leurs congénères où trouver de la nourriture grâce à une danse.",
    "Les éléphants peuvent reconnaître leur reflet dans un miroir.",
    "Les hippocampes mâles portent les œufs jusqu'à leur naissance.",
    "Les papillons goûtent principalement avec leurs pattes.",
    "Les corbeaux peuvent fabriquer et utiliser des outils.",
    "Les loutres de mer utilisent parfois des pierres pour casser des coquillages.",
    "Les chauves-souris sont les seuls mammifères capables de véritable vol actif.",
    "Les baleines à bosse produisent des chants complexes qui peuvent évoluer au fil du temps.",
    "Certaines fourmis peuvent former des ponts vivants avec leur propre corps.",
    "Les escargots peuvent posséder des milliers de petites dents microscopiques.",
    "Les méduses existent depuis bien avant les dinosaures.",
    "Les axolotls peuvent régénérer certaines parties de leur corps.",
    "Le cœur d'une crevette se trouve dans sa tête.",
    "Les papillons monarques peuvent migrer sur plusieurs milliers de kilomètres.",
    "Les chèvres ont des pupilles horizontales.",
    "Les hiboux ne peuvent pas bouger leurs yeux comme les humains et compensent en tournant beaucoup la tête.",
    "Le plus grand animal connu ayant jamais vécu est la baleine bleue.",
    "Les requins peuvent remplacer leurs dents tout au long de leur vie.",
    "Les ours polaires ont une peau sombre sous leur fourrure.",
    "Les manchots ne vivent pas tous en Antarctique.",
    "Les kangourous utilisent leur queue comme appui lorsqu'ils se déplacent.",
    "Les chiens possèdent un odorat beaucoup plus développé que celui des humains.",
    "Les chats utilisent leurs moustaches pour recueillir des informations sur leur environnement.",
    "Les corbeaux sont capables de résoudre certains problèmes en plusieurs étapes.",
    "Les champignons sont biologiquement plus proches des animaux que des plantes.",
    "Les bambous font partie des plantes capables de pousser particulièrement rapidement.",
    "Certaines plantes carnivores peuvent digérer de petits animaux grâce à des enzymes.",
    "Le tournesol jeune suit le déplacement du soleil au cours de la journée.",
    "Les pommes flottent dans l'eau parce qu'elles contiennent beaucoup d'air.",
    "Les cacahuètes sont des légumineuses et non des noix au sens botanique.",
    "Les fraises ne sont pas, botaniquement parlant, de vraies baies.",
    "Les bananes sont considérées comme des baies au sens botanique.",
    "Le café est fabriqué à partir des graines des fruits du caféier.",
    "Le mot « robot » vient du tchèque « robota », qui désigne notamment le travail forcé ou la corvée.",
    "Le premier SMS de l'histoire a été envoyé en 1992.",
    "Le symbole @ est beaucoup plus ancien qu'Internet.",
    "Les premiers ordinateurs électroniques pouvaient occuper des salles entières.",
    "Le papier a été inventé en Chine il y a près de deux mille ans.",
    "L'alphabet braille utilise des combinaisons de points en relief pour représenter les caractères.",
    "Les Romains n'avaient pas de symbole spécifique pour représenter le zéro dans leur système de numération.",
    "La Grande Muraille de Chine est constituée de nombreuses fortifications construites à différentes périodes.",
    "La Tour Eiffel devait initialement être démontée après une période limitée.",
    "Les pyramides de Gizeh ont été construites plusieurs milliers d'années avant l'époque romaine.",
    "Cléopâtre a vécu plus près de l'époque de l'invention de l'iPhone que de la construction des grandes pyramides de Gizeh.",
    "L'Antarctique est le continent le plus froid de la planète.",
    "L'Antarctique est également le plus grand désert du monde selon la définition climatique d'un désert.",
    "Le Sahara n'est donc pas le plus grand désert du monde.",
    "La lumière du Soleil met environ huit minutes pour atteindre la Terre.",
    "La Lune s'éloigne très lentement de la Terre chaque année.",
    "Mars possède le plus grand volcan connu du système solaire : Olympus Mons.",
    "Jupiter est la plus grosse planète du système solaire.",
    "Saturne est moins dense que l'eau en moyenne.",
    "Neptune possède des vents extrêmement rapides.",
    "La Lune joue un rôle majeur dans les marées terrestres.",
    "La Terre est légèrement aplatie aux pôles.",
    "Le son ne peut pas se propager dans le vide.",
    "La glace est moins dense que l'eau liquide, ce qui explique pourquoi elle flotte.",
    "L'eau peut naturellement exister sur Terre sous forme solide, liquide et gazeuse.",
    "La vitesse du son dépend du milieu dans lequel il se propage.",
    "Les arcs-en-ciel sont produits notamment par la réfraction, la réflexion et la dispersion de la lumière.",
    "Un arc-en-ciel est en réalité un cercle complet, mais le sol en masque généralement une partie.",
]


DEVINETTES = [
    {
        "question": "Je suis toujours devant toi, mais tu ne peux jamais me voir. Qui suis-je ?",
        "reponses": ["l'avenir", "avenir"],
    },
    {
        "question": "Plus je sèche, plus je deviens mouillé. Qui suis-je ?",
        "reponses": ["une serviette", "serviette"],
    },
    {
        "question": "Qu'est-ce qui a des dents mais ne peut pas mordre ?",
        "reponses": ["un peigne", "peigne"],
    },
    {
        "question": "Je peux faire le tour du monde en restant dans un coin. Qui suis-je ?",
        "reponses": ["un timbre", "timbre"],
    },
    {
        "question": "Qu'est-ce qui monte mais ne redescend jamais ?",
        "reponses": ["ton âge", "âge", "age"],
    },
    {
        "question": "Plus on m'enlève, plus je deviens grand. Qui suis-je ?",
        "reponses": ["un trou", "trou"],
    },
    {
        "question": "Je suis plein de trous mais je peux retenir de l'eau. Qui suis-je ?",
        "reponses": ["une éponge", "éponge", "eponge"],
    },
    {
        "question": "Qu'est-ce qui a un cou mais pas de tête ?",
        "reponses": ["une bouteille", "bouteille"],
    },
    {
        "question": "Qu'est-ce qui a des mains mais ne peut pas applaudir ?",
        "reponses": ["une horloge", "horloge", "une montre", "montre"],
    },
    {
        "question": "Qu'est-ce qui a une tête et une queue mais pas de corps ?",
        "reponses": ["une pièce", "pièce", "piece"],
    },
    {
        "question": "Qu'est-ce qui peut être cassé sans jamais être touché ?",
        "reponses": ["une promesse", "promesse"],
    },
    {
        "question": "Qu'est-ce qui est à toi mais que les autres utilisent plus que toi ?",
        "reponses": ["ton nom", "nom"],
    },
    {
        "question": "Je grandis sans être vivant et je meurs quand je bois. Qui suis-je ?",
        "reponses": ["le feu", "feu"],
    },
    {
        "question": "Je n'ai pas de bouche mais je peux répondre quand on me parle. Qui suis-je ?",
        "reponses": ["un écho", "écho", "echo"],
    },
    {
        "question": "Je peux être pleine de clés mais je n'ouvre aucune porte. Qui suis-je ?",
        "reponses": ["un clavier", "clavier"],
    },
    {
        "question": "Qu'est-ce qui a des villes mais pas de maisons, des rivières mais pas d'eau et des forêts mais pas d'arbres ?",
        "reponses": ["une carte", "carte", "une carte géographique"],
    },
    {
        "question": "Je suis invisible, mais sans moi tu ne peux pas vivre. Qui suis-je ?",
        "reponses": ["l'air", "air"],
    },
    {
        "question": "Je peux courir sans avoir de jambes. Qui suis-je ?",
        "reponses": ["l'eau", "eau", "une rivière", "rivière"],
    },
    {
        "question": "Qu'est-ce qui a un œil mais ne peut pas voir ?",
        "reponses": ["une aiguille", "aiguille"],
    },
    {
        "question": "Qu'est-ce qui a quatre pieds le matin, deux à midi et trois le soir ?",
        "reponses": ["l'homme", "homme", "un homme", "l'être humain", "être humain"],
    },
    {
        "question": "Je suis plus utile quand je suis cassé. Qui suis-je ?",
        "reponses": ["un œuf", "oeuf", "un oeuf"],
    },
    {
        "question": "Qu'est-ce qui peut remplir une pièce sans prendre de place ?",
        "reponses": ["la lumière", "lumière"],
    },
    {
        "question": "Je disparais dès que tu prononces mon nom. Qui suis-je ?",
        "reponses": ["le silence", "silence"],
    },
    {
        "question": "Qu'est-ce qui a une clé mais n'ouvre aucune serrure ?",
        "reponses": ["un piano", "piano", "un clavier", "clavier"],
    },
    {
        "question": "Qu'est-ce qui tombe sans jamais se faire mal ?",
        "reponses": ["la pluie", "pluie", "la neige", "neige"],
    },
    {
        "question": "Qu'est-ce qui monte quand la pluie descend ?",
        "reponses": ["un parapluie", "parapluie"],
    },
    {
        "question": "Je suis noir quand tu m'achètes, rouge quand tu m'utilises et gris quand tu me jettes. Qui suis-je ?",
        "reponses": ["du charbon", "charbon"],
    },
    {
        "question": "Qu'est-ce qui a beaucoup de lettres mais ne sait pas lire ?",
        "reponses": ["une boîte aux lettres", "boîte aux lettres", "boite aux lettres"],
    },
    {
        "question": "Qu'est-ce qui commence par E, finit par E et ne contient qu'une seule lettre ?",
        "reponses": ["une enveloppe", "enveloppe"],
    },
    {
        "question": "Qu'est-ce qui peut être vu une fois dans une minute, deux fois dans un moment, mais jamais dans mille ans ?",
        "reponses": ["la lettre m", "m"],
    },
    {
        "question": "Quel mois de l'année possède 28 jours ?",
        "reponses": ["tous", "tous les mois", "chaque mois"],
    },
    {
        "question": "Un coq pond un œuf sur le toit d'une maison. De quel côté tombe l'œuf ?",
        "reponses": ["aucun", "un coq ne pond pas d'oeufs", "le coq ne pond pas"],
    },
    {
        "question": "Tu me casses avant de m'utiliser. Qui suis-je ?",
        "reponses": ["un œuf", "oeuf", "un oeuf"],
    },
    {
        "question": "Plus tu en prends, plus tu en laisses derrière toi. Que sont-elles ?",
        "reponses": ["des empreintes", "empreintes", "des pas", "pas"],
    },
    {
        "question": "Qu'est-ce qui peut être attrapé mais jamais lancé ?",
        "reponses": ["un rhume", "rhume"],
    },
    {
        "question": "Qu'est-ce qui a une bouche mais ne mange jamais ?",
        "reponses": ["une rivière", "rivière", "un fleuve", "fleuve"],
    },
]


# Devinette actuellement en cours
_devinette_actuelle = None


def normaliser_texte(texte):
    """
    Nettoie un texte pour faciliter la comparaison des réponses.
    """
    texte = texte.lower().strip()

    texte = unicodedata.normalize("NFD", texte)
    texte = "".join(
        caractere
        for caractere in texte
        if unicodedata.category(caractere) != "Mn"
    )

    texte = re.sub(r"[^\w\s]", "", texte)
    texte = re.sub(r"\s+", " ", texte)

    return texte.strip()


def blague():
    """Retourne une blague aléatoire."""
    return random.choice(BLAGUES)


def anecdote():
    """Retourne une anecdote aléatoire."""
    return random.choice(ANECDOTES)


def commencer_devinette():
    """
    Commence une nouvelle devinette.

    La réponse n'est pas donnée immédiatement.
    """
    global _devinette_actuelle

    _devinette_actuelle = random.choice(DEVINETTES)

    return _devinette_actuelle["question"]


def verifier_devinette(reponse_utilisateur):
    """
    Vérifie la réponse de l'utilisateur à la devinette actuelle.
    """

    global _devinette_actuelle

    if _devinette_actuelle is None:
        return "Je ne t'ai pas posé de devinette."

    reponse_utilisateur = normaliser_texte(reponse_utilisateur)

    reponses_correctes = [
        normaliser_texte(reponse)
        for reponse in _devinette_actuelle["reponses"]
    ]

    if reponse_utilisateur in reponses_correctes:
        resultat = "Bravo ! Bonne réponse !"
    else:
        bonne_reponse = _devinette_actuelle["reponses"][0]
        resultat = f"Raté ! La bonne réponse était {bonne_reponse}."

    _devinette_actuelle = None

    return resultat


def devinette_en_cours():
    """
    Indique si DeskBot attend actuellement une réponse.
    """
    return _devinette_actuelle is not None


def divertissement(type_divertissement):
    """
    Lance un divertissement.

    Types :
    - blague
    - anecdote
    - devinette
    """

    type_divertissement = type_divertissement.lower().strip()

    if type_divertissement == "blague":
        return blague()

    elif type_divertissement == "anecdote":
        return anecdote()

    elif type_divertissement == "devinette":
        return commencer_devinette()

    return "Je ne connais pas ce type de divertissement."