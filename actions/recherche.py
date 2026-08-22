from ddgs import DDGS
from deep_translator import GoogleTranslator


def _rechercher(requete, nombre=3):
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(requete, region="fr-fr", max_results=nombre))
    except Exception as e:
        print("Erreur recherche :", e)
        return []


def _premier_paragraphe(texte, max_caracteres=500):
    """Coupe au premier vrai paragraphe, ou a defaut a la derniere
    phrase complete avant max_caracteres."""

    texte = texte.strip()

    if "\n\n" in texte:
        texte = texte.split("\n\n")[0]

    if len(texte) > max_caracteres:
        tronque = texte[:max_caracteres]
        dernier_point = tronque.rfind(". ")
        texte = tronque[:dernier_point + 1] if dernier_point > 100 else tronque + "..."

    return texte


def _traduire_en_francais(texte):
    if not texte:
        return texte
    try:
        return GoogleTranslator(source="auto", target="fr").translate(texte)
    except Exception as e:
        print("Erreur traduction :", e)
        return texte  # on renvoie l'original plutot que de tout casser


def rechercher_paragraphe(requete):
    resultats = _rechercher(requete, nombre=1)
    if not resultats:
        return None

    texte = _premier_paragraphe(resultats[0].get("body", ""))
    return _traduire_en_francais(texte)


def rechercher_resultat(requete, numero):
    resultats = _rechercher(requete, nombre=max(numero, 3))
    index = numero - 1

    if index < 0 or index >= len(resultats):
        return None

    resultat = resultats[index]
    titre = _traduire_en_francais(resultat.get("title", ""))

    return titre, resultat.get("href", "")