import re
from deep_translator import GoogleTranslator


LANGUES = {
    "français": "fr",
    "francais": "fr",
    "anglais": "en",
    "espagnol": "es",
    "allemand": "de",
    "italien": "it",
    "portugais": "pt",
    "néerlandais": "nl",
    "polonais": "pl",
    "russe": "ru",
    "ukrainien": "uk",
    "arabe": "ar",
    "chinois": "zh-CN",
    "japonais": "ja",
    "coréen": "ko",
    "coreen": "ko",
}

LANGUE_ACTUELLE = "fr"

def definir_langue(langue):
    global LANGUE_ACTUELLE
    LANGUE_ACTUELLE = langue

def retourner_langue():
    return LANGUE_ACTUELLE

def extraire_traduction(texte):
    for langue, code in sorted(
        LANGUES.items(),
        key=lambda x: len(x[0]),
        reverse=True
    ):

        match = re.search(
            rf"\s+(?:en|vers|dans)\s+{re.escape(langue)}\s*$",
            texte,
            re.IGNORECASE
        )

        if match:

            texte_a_traduire = texte[:match.start()].strip()

            texte_a_traduire = re.sub(
                r"^(?:traduis|traduit|traduire|traduction)\s+",
                "",
                texte_a_traduire,
                flags=re.IGNORECASE
            ).strip()

            return texte_a_traduire, code

    return None, None


def traduire(texte, langue):
    try:
        return GoogleTranslator(
            source="auto",
            target=langue
        ).translate(texte)

    except Exception as e:
        print("Erreur traduction :", e)
        return "Je n'ai pas réussi à effectuer la traduction."


def traiter_traduction(texte):
    global LANGUE_ACTUELLE

    texte_a_traduire, langue = extraire_traduction(texte)

    if not texte_a_traduire:
        return "Je n'ai pas compris ce que tu veux traduire."

    if not langue:
        return "Je n'ai pas compris la langue cible."

    resultat = traduire(
        texte_a_traduire,
        langue
    )

    # On indique à voix.py quelle langue utiliser
    LANGUE_ACTUELLE = langue

    return resultat