import requests
import re
from datetime import date

JOURS_SEMAINE = [
    "lundi", "mardi", "mercredi", "jeudi",
    "vendredi", "samedi", "dimanche"
]

MOIS = {
    "janvier": 1, "fevrier": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "aout": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12
}

NOMS_OFFICIELS = {
    "etables sur mer": "Étables-sur-Mer",
    "saintes maries de la mer": "Saintes-Maries-de-la-Mer",
    "hebecourt": "Hébécourt",
    "fontvieille": "Fontvieille",
    "gisors": "Gisors",
    "binic": "Binic",
    "montreuil": "Montreuil",
}

def extraire_jour_cible(texte, aujourdhui=None):

    if aujourdhui is None:
        aujourdhui = date.today()

    if "apres demain" in texte or "apres-demain" in texte:
        return 2

    if "demain" in texte:
        return 1

    if "aujourd'hui" in texte or "aujourdhui" in texte:
        return 0

    # Format ISO envoyé par le champ <input type="date"> du site : AAAA-MM-JJ
    # Placé en priorité car sans ambiguïté (4 chiffres d'année),
    # contrairement au format JJ/MM qui peut se confondre avec lui.
    match_iso = re.search(r"(\d{4})-(\d{2})-(\d{2})", texte)
    if match_iso:
        annee, mois_num, jour_num = map(int, match_iso.groups())
        try:
            cible = date(annee, mois_num, jour_num)
        except ValueError:
            return None
        return (cible - aujourdhui).days

    for i, jour in enumerate(JOURS_SEMAINE):
        if jour in texte:
            decalage = (i - aujourdhui.weekday()) % 7
            return decalage if decalage != 0 else 7

    match = re.search(r"(\d{1,2})\s+(" + "|".join(MOIS.keys()) + r")", texte)
    if match:
        jour_num = int(match.group(1))
        mois_num = MOIS[match.group(2)]
        try:
            cible = date(aujourdhui.year, mois_num, jour_num)
        except ValueError:
            return None
        if cible < aujourdhui:
            cible = cible.replace(year=aujourdhui.year + 1)
        return (cible - aujourdhui).days

    # Format vocal JJ/MM ou JJ-MM (sans année ISO)
    match_slash = re.search(r"(\d{1,2})[/\-](\d{1,2})(?:[/\-](\d{2,4}))?", texte)
    if match_slash:
        jour_num = int(match_slash.group(1))
        mois_num = int(match_slash.group(2))

        annee = aujourdhui.year
        if match_slash.group(3):
            annee = int(match_slash.group(3))
            if annee < 100:
                annee += 2000

        try:
            cible = date(annee, mois_num, jour_num)
        except ValueError:
            return None

        if cible < aujourdhui and not match_slash.group(3):
            cible = cible.replace(year=aujourdhui.year + 1)

        return (cible - aujourdhui).days

    return None

CODES_METEO = {
    0: "le ciel est parfaitement dégagé",
    1: "le ciel est principalement dégagé",
    2: "il y a quelques nuages",
    3: "le ciel est couvert",
    45: "il y a du brouillard",
    48: "il y a du brouillard givrant",
    51: "il tombe une légère bruine",
    53: "il tombe une bruine modérée",
    55: "il tombe une forte bruine",
    56: "il tombe une bruine verglaçante",
    57: "il tombe une forte bruine verglaçante",
    61: "il pleut faiblement",
    63: "il pleut modérément",
    65: "il pleut fortement",
    66: "il pleut avec du verglas",
    67: "il pleut fortement avec du verglas",
    71: "il neige légèrement",
    73: "il neige modérément",
    75: "il neige fortement",
    77: "il y a des grains de neige",
    80: "il y a quelques averses",
    81: "il y a des averses modérées",
    82: "il y a de fortes averses",
    85: "il y a quelques averses de neige",
    86: "il y a de fortes averses de neige",
    95: "il y a de l'orage",
    96: "il y a de l'orage avec de la grêle",
    99: "il y a un violent orage avec de la grêle",
}

CODES_METEO_FUTUR = {
    0: "le ciel sera parfaitement dégagé",
    1: "le ciel sera principalement dégagé",
    2: "il y aura quelques nuages",
    3: "le ciel sera couvert",
    45: "il y aura du brouillard",
    48: "il y aura du brouillard givrant",
    51: "il tombera une légère bruine",
    53: "il tombera une bruine modérée",
    55: "il tombera une forte bruine",
    56: "il tombera une bruine verglaçante",
    57: "il tombera une forte bruine verglaçante",
    61: "il pleuvra faiblement",
    63: "il pleuvra modérément",
    65: "il pleuvra fortement",
    66: "il pleuvra avec du verglas",
    67: "il pleuvra fortement avec du verglas",
    71: "il neigera légèrement",
    73: "il neigera modérément",
    75: "il neigera fortement",
    77: "il y aura des grains de neige",
    80: "il y aura quelques averses",
    81: "il y aura des averses modérées",
    82: "il y aura de fortes averses",
    85: "il y aura quelques averses de neige",
    86: "il y aura de fortes averses de neige",
    95: "il y aura de l'orage",
    96: "il y aura de l'orage avec de la grêle",
    99: "il y aura un violent orage avec de la grêle",
}

def obtenir_position():
    try:
        reponse = requests.get("http://ip-api.com/json/", timeout=5)
        data = reponse.json()

        if data["status"] == "success":
            return data["lat"], data["lon"]

    except Exception as e:
        print("Erreur géolocalisation :", e)

    return None, None

def meteo_ici(jour_offset=0):
    latitude, longitude = obtenir_position()

    if latitude is None:
        return "Je n'ai pas réussi à obtenir votre position."

    if jour_offset == 0:
        return meteo_coordonnees(latitude, longitude)

    jour_offset = min(jour_offset, 15)

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}"
        f"&longitude={longitude}"
        "&daily="
        "temperature_2m_max,"
        "apparent_temperature_max,"
        "relative_humidity_2m_mean,"
        "weather_code,"
        "wind_speed_10m_max"
        "&timezone=auto"
        f"&forecast_days={jour_offset + 1}"
    )

    reponse = requests.get(url)

    if reponse.status_code != 200:
        return "Impossible de récupérer la météo."

    quotidien = reponse.json()["daily"]

    if jour_offset >= len(quotidien["time"]):
        return "Je ne peux pas prévoir la météo aussi loin."

    return _formuler_meteo(
        "votre position",
        quotidien["temperature_2m_max"][jour_offset],
        quotidien["apparent_temperature_max"][jour_offset],
        quotidien["relative_humidity_2m_mean"][jour_offset],
        quotidien["wind_speed_10m_max"][jour_offset],
        quotidien["weather_code"][jour_offset],
        jour_offset
    )

def meteo_coordonnees(latitude, longitude, nom="votre position"):

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}"
        f"&longitude={longitude}"
        "&current="
        "temperature_2m,"
        "apparent_temperature,"
        "relative_humidity_2m,"
        "weather_code,"
        "wind_speed_10m"
    )

    reponse = requests.get(url)

    if reponse.status_code != 200:
        return "Impossible de récupérer la météo."

    meteo = reponse.json()["current"]

    temperature = meteo["temperature_2m"]
    ressentie = meteo["apparent_temperature"]
    humidite = meteo["relative_humidity_2m"]
    vent = meteo["wind_speed_10m"]
    code = meteo["weather_code"]

    description = CODES_METEO.get(code, "le temps est inconnu")

    if round(temperature) < 8:
        conseils_vestimentaires = "Je te conseille de porter un jogging chaud, un t-shirt à manches longues, un pull, une veste chaude et des accessoires adaptés au froid (bonnet, gants, etc...)"
    elif round(temperature) < 13:
        conseils_vestimentaires = "Je te conseille de porter un jogging chaud, un t-shirt à manches longues, un pull et une veste chaude"
    elif round(temperature) < 18:
        conseils_vestimentaires = "Je te conseille de porter un jogging, un t-shirt à manches longues et un pull ou un gilet"
    elif round(temperature) < 21:
        conseils_vestimentaires = "Je te conseille de porter un jogging et un t-shirt à manches longues"
    elif round(temperature) < 25:
        conseils_vestimentaires = "Je te conseille de porter un short et un t-shirt à manches courtes"
    else:
        conseils_vestimentaires = "Je te conseille de porter un short, un t-shirt à manches courtes, une casquette, des lunettes de soleil et de penser à boire"

    avertissement = ""

    if code in [61, 63, 65, 80, 81, 82]:
        avertissement = "N'oublie pas de prendre un parapluie, car il risque de pleuvoir."
    elif code in [71, 73, 75, 77, 85, 86]:
        avertissement = "Fais attention, il risque de neiger."
    elif code in [95, 96, 99]:
        avertissement = "Attention aux orages et à la grêle."
    elif code in [45, 48]:
        avertissement = "La visibilité est réduite à cause du brouillard."
    elif code in [0, 1, 2, 3]:
        avertissement = "Profite du beau temps !"
    elif code in [56, 57]:
        avertissement = "Fais attention, il risque de pleuvoir avec du verglas."
    else:
        avertissement = "Il n'y a pas d'avertissement particulier pour le moment."

    return (
        f"À {nom}, il fait {round(temperature)} degrés et {description}. "
        f"La température ressentie est de {round(ressentie)} degrés. "
        f"L'humidité est de {humidite} pour cent et le vent souffle à {round(vent)} kilomètres par heure. "
        f"{conseils_vestimentaires}. "
        f"{avertissement}"
    )

def meteo(ville, jour_offset=0):

    print("Ville reçue :", ville)

    ville_recherche = NOMS_OFFICIELS.get(ville.lower().strip(), ville)

    url = (
        "https://geocoding-api.open-meteo.com/v1/search"
        f"?name={ville_recherche}&count=1&language=fr&format=json"
    )
    reponse = requests.get(url)

    if reponse.status_code != 200:
        return "Impossible de contacter le service météo."

    donnees = reponse.json()

    if "results" not in donnees:
        return "Je n'ai pas trouvé cette ville."

    resultat = donnees["results"][0]
    latitude = resultat["latitude"]
    longitude = resultat["longitude"]
    nom = resultat["name"]

    # ---------------------------------------------------
    # Jour même : données "current"
    # ---------------------------------------------------

    if jour_offset == 0:

        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={latitude}"
            f"&longitude={longitude}"
            "&current="
            "temperature_2m,"
            "apparent_temperature,"
            "relative_humidity_2m,"
            "weather_code,"
            "wind_speed_10m"
        )

        reponse = requests.get(url)

        if reponse.status_code != 200:
            return "Impossible de récupérer la météo."

        actuel = reponse.json()["current"]

        return _formuler_meteo(
            nom,
            actuel["temperature_2m"],
            actuel["apparent_temperature"],
            actuel["relative_humidity_2m"],
            actuel["wind_speed_10m"],
            actuel["weather_code"],
            jour_offset
        )

    # ---------------------------------------------------
    # Jour futur : données "daily", mais MÊME formulation
    # ---------------------------------------------------

    jour_offset = min(jour_offset, 15)

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}"
        f"&longitude={longitude}"
        "&daily="
        "temperature_2m_max,"
        "apparent_temperature_max,"
        "relative_humidity_2m_mean,"
        "weather_code,"
        "wind_speed_10m_max"
        "&timezone=auto"
        f"&forecast_days={jour_offset + 1}"
    )

    reponse = requests.get(url)

    if reponse.status_code != 200:
        return "Impossible de récupérer la météo."

    quotidien = reponse.json()["daily"]

    if jour_offset >= len(quotidien["time"]):
        return "Je ne peux pas prévoir la météo aussi loin."

    return _formuler_meteo(
        nom,
        quotidien["temperature_2m_max"][jour_offset],
        quotidien["apparent_temperature_max"][jour_offset],
        quotidien["relative_humidity_2m_mean"][jour_offset],
        quotidien["wind_speed_10m_max"][jour_offset],
        quotidien["weather_code"][jour_offset],
        jour_offset
    )

def _conseils_vestimentaires(temperature):

    if round(temperature) < 8:
        return "Je te conseille de porter un jogging chaud, un t-shirt à manches longues, un pull, une veste chaude et des accessoires adaptés au froid (bonnet, gants, etc...)"
    elif round(temperature) < 13:
        return "Je te conseille de porter un jogging chaud, un t-shirt à manches longues, un pull et une veste chaude"
    elif round(temperature) < 18:
        return "Je te conseille de porter un jogging, un t-shirt à manches longues et un pull ou un gilet"
    elif round(temperature) < 21:
        return "Je te conseille de porter un jogging et un t-shirt à manches longues"
    elif round(temperature) < 25:
        return "Je te conseille de porter un short et un t-shirt à manches courtes"
    else:
        return "Je te conseille de porter un short, un t-shirt à manches courtes, une casquette, des lunettes de soleil et de penser à boire"


def _avertissement(code):

    if code in [61, 63, 65, 80, 81, 82]:
        return "N'oublie pas de prendre un parapluie, car il risque de pleuvoir."
    elif code in [71, 73, 75, 77, 85, 86]:
        return "Fais attention, il risque de neiger."
    elif code in [95, 96, 99]:
        return "Attention aux orages et à la grêle."
    elif code in [45, 48]:
        return "La visibilité est réduite à cause du brouillard."
    elif code in [0, 1, 2, 3]:
        return "Profite du beau temps !"
    elif code in [56, 57]:
        return "Fais attention, il risque de pleuvoir avec du verglas."
    else:
        return "Il n'y a pas d'avertissement particulier pour le moment."
    
def _avertissement_futur(code):

    if code in [61, 63, 65, 80, 81, 82]:
        return "N'oublie pas de prendre un parapluie, car il y aura un risque de pluie."
    elif code in [71, 73, 75, 77, 85, 86]:
        return "Fais attention, il y aura un risque de neige."
    elif code in [95, 96, 99]:
        return "Attention aux orages et à la grêle."
    elif code in [45, 48]:
        return "La visibilité sera réduite à cause du brouillard."
    elif code in [0, 1, 2, 3]:
        return "Tu pourras profiter du beau temps !"
    elif code in [56, 57]:
        return "Fais attention, il y aura un risque de pluie avec du verglas."
    else:
        return "Il n'y a pas d'avertissement particulier pour le moment."

def _formuler_meteo(nom, temperature, ressentie, humidite, vent, code, jour_offset=0):

    conseils_vestimentaires = _conseils_vestimentaires(temperature)

    if jour_offset == 0:
        verbe_faire = "il fait"
        verbe_etre = "est"
        avertissement = _avertissement(code)
        description = CODES_METEO.get(code, "le temps est inconnu")
    else:
        verbe_faire = "il fera"
        verbe_etre = "sera"
        avertissement = _avertissement_futur(code)
        description = CODES_METEO_FUTUR.get(code, "le temps est inconnu")

    return (
        f"À {nom}, {verbe_faire} {round(temperature)} degrés et {description}. "
        f"La température ressentie {verbe_etre} de {round(ressentie)} degrés. "
        f"L'humidité {verbe_etre} de {round(humidite)} pour cent et le vent soufflera à {round(vent)} kilomètres par heure. "
        f"{conseils_vestimentaires}. "
        f"{avertissement}"
    )