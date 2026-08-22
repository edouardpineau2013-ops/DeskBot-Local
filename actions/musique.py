from rapidfuzz import process
from yt_dlp import YoutubeDL
import vlc

# Lecteur global
player = None

MUSIQUES = {
    "lofi relax": "https://www.youtube.com/watch?v=cyzx45mupcQ",
    "lofi pour coder": "https://www.youtube.com/watch?v=fhL67fnDXcU",
    "lofi pour travailler": "https://www.youtube.com/watch?v=JCKBaJDRMw4",
    "lofi pour dormir": "https://www.youtube.com/watch?v=eTP5PZ8NoeU",
    "lofi pour se concentrer": "https://www.youtube.com/watch?v=8b3fqIBrNW0",
    "lofi gaming": "https://www.youtube.com/watch?v=cyzx45mupcQ",
}

def jouer_musique(texte):
    global player

    texte = texte.lower()

    # Enlever les mots inutiles
    for mot in [
        "mets",
        "met",
        "joue",
        "lance",
        "écoute",
        "musique"
    ]:
        texte = texte.replace(mot, "")

    texte = texte.strip()

    resultat = process.extractOne(
        texte,
        MUSIQUES.keys(),
        score_cutoff=60
    )

    if resultat is None:
        return "Je ne connais pas cette musique."

    nom = resultat[0]
    url = MUSIQUES[nom]

    ydl_opts = {
        "format": "bestaudio",
        "quiet": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_url = info["url"]

    if player is not None:
        player.stop()

    instance = vlc.Instance("--no-video")
    media = instance.media_new(audio_url)

    player = instance.media_player_new()
    player.set_media(media)
    player.play()

    return f"Je lance {nom}."

def arreter_musique():
    global player

    if player is not None:
        player.stop()
        return "Musique arrêtée."

    return "Aucune musique n'est en cours."

def pause_musique():
    global player

    if player is not None:
        player.pause()
        return "Musique en pause."

    return "Aucune musique."

def volume_musique(volume):
    global player

    if player is None:
        return "Aucune musique."

    volume = max(0, min(100, volume))
    player.audio_set_volume(volume)

    return f"Volume réglé à {volume} pour cent."

def augmenter_volume(pas=10):
    global player

    if player is None:
        return "Aucune musique."

    volume_actuel = player.audio_get_volume()
    nouveau_volume = max(0, min(100, volume_actuel + pas))
    player.audio_set_volume(nouveau_volume)

    return f"Volume monté à {nouveau_volume} pour cent."


def diminuer_volume(pas=10):
    global player

    if player is None:
        return "Aucune musique."

    volume_actuel = player.audio_get_volume()
    nouveau_volume = max(0, min(100, volume_actuel - pas))
    player.audio_set_volume(nouveau_volume)

    return f"Volume baissé à {nouveau_volume} pour cent."