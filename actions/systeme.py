from rapidfuzz import process

COMMANDES_SYSTEME = {
    "google": [
        "ouvre google",
        "google",
        "va sur google",
        "lance google"
    ],

    "youtube": [
        "ouvre youtube",
        "youtube",
        "va sur youtube",
        "lance youtube"
    ],

    "calculatrice": [
        "ouvre la calculatrice",
        "calculatrice",
        "lance la calculatrice"
    ]
}

from rapidfuzz import process, fuzz

def executer(texte):

    phrases = []

    for nom, variantes in COMMANDES_SYSTEME.items():
        for variante in variantes:
            phrases.append((variante, nom))

    meilleure = process.extractOne(
        texte,
        [p[0] for p in phrases],
        scorer=fuzz.ratio
    )

    if meilleure is None:
        return None

    phrase, score, _ = meilleure

    if score < 75:
        return None

    commande = next(n for p, n in phrases if p == phrase)

    import webbrowser
    import os

    if commande == "google":
        webbrowser.open("https://google.com")
        return "J'ouvre Google."

    if commande == "youtube":
        webbrowser.open("https://youtube.com")
        return "J'ouvre YouTube."

    if commande == "calculatrice":
        os.system("calc")
        return "J'ouvre la calculatrice."

    return None