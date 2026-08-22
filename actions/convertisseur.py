import re
import requests
from functools import lru_cache


API_URL = "https://api.frankfurter.dev/v2"


UNITES = {
    "longueur": {
        "mm": 0.001,
        "millimètre": 0.001,
        "millimètres": 0.001,
        "cm": 0.01,
        "centimètre": 0.01,
        "centimètres": 0.01,
        "m": 1,
        "mètre": 1,
        "mètres": 1,
        "km": 1000,
        "kilomètre": 1000,
        "kilomètres": 1000,
        "in": 0.0254,
        "inch": 0.0254,
        "pouce": 0.0254,
        "pouces": 0.0254,
        "ft": 0.3048,
        "pied": 0.3048,
        "pieds": 0.3048,
        "yd": 0.9144,
        "yard": 0.9144,
        "yards": 0.9144,
        "mile": 1609.344,
        "miles": 1609.344
    },

    "masse": {
        "mg": 0.000001,
        "milligramme": 0.000001,
        "milligrammes": 0.000001,
        "g": 0.001,
        "gramme": 0.001,
        "grammes": 0.001,
        "kg": 1,
        "kilogramme": 1,
        "kilogrammes": 1,
        "t": 1000,
        "tonne": 1000,
        "tonnes": 1000,
        "oz": 0.0283495,
        "once": 0.0283495,
        "onces": 0.0283495,
        "lb": 0.453592,
        "livre": 0.453592,
        "livres": 0.453592
    },

    "volume": {
        "ml": 0.001,
        "millilitre": 0.001,
        "millilitres": 0.001,
        "cl": 0.01,
        "centilitre": 0.01,
        "centilitres": 0.01,
        "dl": 0.1,
        "décilitre": 0.1,
        "décilitres": 0.1,
        "l": 1,
        "litre": 1,
        "litres": 1,
        "m3": 1000,
        "mètre cube": 1000,
        "mètres cubes": 1000,
        "gal": 3.785411784,
        "gallon": 3.785411784,
        "gallons": 3.785411784
    },

    "surface": {
        "mm2": 0.000001,
        "cm2": 0.0001,
        "m2": 1,
        "km2": 1000000,
        "hectare": 10000,
        "hectares": 10000,
        "ha": 10000,
        "acre": 4046.8564224,
        "acres": 4046.8564224
    },

    "vitesse": {
        "m/s": 1,
        "m/s": 1,
        "km/h": 1 / 3.6,
        "kmh": 1 / 3.6,
        "mph": 0.44704,
        "mile/h": 0.44704,
        "noeud": 0.514444,
        "noeuds": 0.514444,
        "knot": 0.514444,
        "knots": 0.514444
    },

    "temps": {
        "ms": 0.001,
        "milliseconde": 0.001,
        "millisecondes": 0.001,
        "s": 1,
        "sec": 1,
        "seconde": 1,
        "secondes": 1,
        "min": 60,
        "minute": 60,
        "minutes": 60,
        "h": 3600,
        "heure": 3600,
        "heures": 3600,
        "jour": 86400,
        "jours": 86400,
        "semaine": 604800,
        "semaines": 604800
    }
}


MONNAIES = {
    "€": "EUR",
    "euro": "EUR",
    "euros": "EUR",
    "eur": "EUR",

    "$": "USD",
    "dollar": "USD",
    "dollars": "USD",
    "usd": "USD",

    "£": "GBP",
    "livre sterling": "GBP",
    "livres sterling": "GBP",
    "livre": "GBP",
    "livres": "GBP",
    "gbp": "GBP",

    "¥": "JPY",
    "yen": "JPY",
    "yens": "JPY",
    "jpy": "JPY",

    "franc suisse": "CHF",
    "francs suisses": "CHF",
    "chf": "CHF",

    "dollar canadien": "CAD",
    "dollars canadiens": "CAD",
    "cad": "CAD",

    "dollar australien": "AUD",
    "dollars australiens": "AUD",
    "aud": "AUD",

    "yuan": "CNY",
    "yuans": "CNY",
    "renminbi": "CNY",
    "cny": "CNY",

    "couronne danoise": "DKK",
    "couronnes danoises": "DKK",
    "dkk": "DKK",

    "couronne suédoise": "SEK",
    "couronnes suédoises": "SEK",
    "sek": "SEK",

    "couronne norvégienne": "NOK",
    "couronnes norvégiennes": "NOK",
    "nok": "NOK",

    "zloty": "PLN",
    "zlotys": "PLN",
    "pln": "PLN",

    "couronne tchèque": "CZK",
    "couronnes tchèques": "CZK",
    "czk": "CZK",

    "forint": "HUF",
    "forints": "HUF",
    "huf": "HUF",

    "livre turque": "TRY",
    "livres turques": "TRY",
    "try": "TRY",

    "real brésilien": "BRL",
    "reals brésiliens": "BRL",
    "brl": "BRL",

    "rouble": "RUB",
    "roubles": "RUB",
    "rub": "RUB"
}


SYMBOLES_MONNAIES = {
    "EUR": "€",
    "USD": "$",
    "GBP": "£",
    "JPY": "¥",
    "CHF": "CHF",
    "CAD": "CA$",
    "AUD": "A$",
    "CNY": "¥",
    "DKK": "kr",
    "SEK": "kr",
    "NOK": "kr",
    "PLN": "zł",
    "CZK": "Kč",
    "HUF": "Ft",
    "TRY": "₺",
    "BRL": "R$",
    "RUB": "₽"
}


def normaliser(texte):
    return texte.lower().strip()


def trouver_unite(texte):
    texte = normaliser(texte)
    toutes_les_unites = {}

    for categorie, unites in UNITES.items():
        for unite in unites:
            toutes_les_unites[unite] = categorie

    correspondances = []

    for unite, categorie in toutes_les_unites.items():
        match = re.search(
            r"(?<!\w)" + re.escape(unite) + r"(?!\w)",
            texte
        )

        if match:
            correspondances.append(
                (match.start(), -len(unite), unite, categorie)
            )

    if not correspondances:
        return None, None

    correspondances.sort()

    _, _, unite, categorie = correspondances[0]

    return unite, categorie


def trouver_monnaie(texte):
    texte = normaliser(texte)

    for monnaie in sorted(MONNAIES, key=len, reverse=True):
        if monnaie in texte:
            return MONNAIES[monnaie]

    return None


def convertir_unite(valeur, unite_depart, unite_arrivee):
    unite_depart = normaliser(unite_depart)
    unite_arrivee = normaliser(unite_arrivee)

    unite_dep, categorie_dep = trouver_unite(unite_depart)
    unite_arr, categorie_arr = trouver_unite(unite_arrivee)

    if not unite_dep or not unite_arr:
        raise ValueError("Unité inconnue.")

    if categorie_dep != categorie_arr:
        raise ValueError("Les deux unités ne sont pas compatibles.")

    valeur_base = valeur * UNITES[categorie_dep][unite_dep]
    resultat = valeur_base / UNITES[categorie_arr][unite_arr]

    return resultat


@lru_cache(maxsize=100)
def obtenir_taux(depart, arrivee):
    depart = depart.upper()
    arrivee = arrivee.upper()

    if depart == arrivee:
        return 1.0

    url = f"{API_URL}/rate/{depart}/{arrivee}"

    try:
        reponse = requests.get(url, timeout=5)
        reponse.raise_for_status()

        donnees = reponse.json()

        return float(donnees["rate"])

    except requests.RequestException as e:
        raise ConnectionError(
            "Impossible de récupérer le taux de change."
        ) from e

    except (KeyError, ValueError):
        raise ConnectionError(
            "Réponse invalide de l'API de change."
        )


def convertir_monnaie(valeur, monnaie_depart, monnaie_arrivee):
    depart = trouver_monnaie(monnaie_depart)
    arrivee = trouver_monnaie(monnaie_arrivee)

    if not depart:
        depart = monnaie_depart.upper()

    if not arrivee:
        arrivee = monnaie_arrivee.upper()

    taux = obtenir_taux(depart, arrivee)

    return valeur * taux


def symbole_monnaie(code):
    return SYMBOLES_MONNAIES.get(code.upper(), code.upper())


def extraire_nombre(texte):
    texte = texte.replace(",", ".")

    match = re.search(
        r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)",
        texte
    )

    if not match:
        raise ValueError("Aucun nombre trouvé.")

    return float(match.group())


def convertir(texte):
    texte = normaliser(texte)
    valeur = extraire_nombre(texte)

    # =========================================================
    # CONVERSION DE MONNAIE
    # =========================================================

    monnaies_trouvees = []

    for nom, code in MONNAIES.items():
        if nom in ["€", "$", "£", "¥"]:
            position = texte.find(nom)
        else:
            match = re.search(
                r"(?<!\w)" + re.escape(nom) + r"(?!\w)",
                texte
            )
            position = match.start() if match else -1

        if position != -1:
            monnaies_trouvees.append((position, code))

    monnaies_uniques = []

    for position, code in sorted(monnaies_trouvees):
        if not any(c == code for _, c in monnaies_uniques):
            monnaies_uniques.append((position, code))

    if len(monnaies_uniques) >= 2:
        depart = monnaies_uniques[0][1]
        arrivee = monnaies_uniques[1][1]

        resultat = convertir_monnaie(
            valeur,
            depart,
            arrivee
        )

        return (
            f"{valeur:g} {symbole_monnaie(depart)} = "
            f"{resultat:.2f} {symbole_monnaie(arrivee)}"
        )

    # =========================================================
    # CONVERSION D'UNITÉ
    # =========================================================

    unite_depart, categorie_depart = trouver_unite(texte)

    if not unite_depart:
        return ("Je n'ai pas reconnu l'unité de départ.")

    match_arrivee = re.search(
        r"\b(?:en|vers|à|a|dans|pour)\s+(.+)$",
        texte
    )

    if not match_arrivee:
        return ("Je n'ai pas reconnu l'unité d'arrivée.")

    texte_arrivee = match_arrivee.group(1).strip()

    unite_arrivee = None

    for unite in sorted(
        UNITES[categorie_depart],
        key=len,
        reverse=True
    ):
        if re.search(
            r"(?<!\w)" + re.escape(unite) + r"(?!\w)",
            texte_arrivee
        ):
            unite_arrivee = unite
            break

    if not unite_arrivee:
        return ("La conversion n'est pas possible.")

    resultat = convertir_unite(
        valeur,
        unite_depart,
        unite_arrivee
    )

    return (
        f"{valeur:g} {unite_depart} = "
        f"{resultat:g} {unite_arrivee}"
    )



def vider_cache_taux():
    obtenir_taux.cache_clear()


if __name__ == "__main__":
    exemples = [
        "convertis 10 km en mètres",
        "convertis 500 grammes en kilogrammes",
        "convertis 2 litres en millilitres",
        "convertis 100 km/h en mph",
        "convertis 20 euros en dollars",
        "convertis 50 dollars en euros",
        "convertis 100 livres sterling en euros"
    ]

    for exemple in exemples:
        try:
            print(convertir(exemple))
        except Exception as e:
            print(f"Erreur : {e}")