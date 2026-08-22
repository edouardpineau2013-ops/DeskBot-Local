import asyncio
import edge_tts
import pygame
import os
import tempfile
import uuid
import requests
from etat_deskbot import definir_etat
from actions.traduction import retourner_langue

TOPIC_NTFY = "deskbot_notifs"


# Initialisation du lecteur audio
pygame.mixer.init()

VOIX = "fr-FR-DeniseNeural"

VOIX_LANGUES = {
    "fr": "fr-FR-DeniseNeural",
    "en": "en-US-JennyNeural",
    "de": "de-DE-KatjaNeural",
    "es": "es-ES-ElviraNeural",
    "it": "it-IT-ElsaNeural",
    "ja": "ja-JP-NanamiNeural",
    "ko": "ko-KR-SunHiNeural",
    "zh-CN": "zh-CN-XiaoxiaoNeural",
}


async def generer_audio(texte):

    fichier = os.path.join(
        tempfile.gettempdir(),
        f"deskbot_{uuid.uuid4()}.mp3"
    )

    langue = retourner_langue()

    voix = VOIX_LANGUES.get(
        langue,
        VOIX
    )

    communication = edge_tts.Communicate(
        texte,
        voix
    )

    await communication.save(fichier)

    return fichier

def notifier_telephone(titre, message):
    try:
        requests.post(
            f"https://ntfy.sh/{TOPIC_NTFY}",
            data=message.encode("utf-8"),
            headers={"Title": titre.encode("utf-8")},
            timeout=5
        )
    except Exception as e:
        print("Erreur notification ntfy :", e)

def jouer_son(chemin):
        son = pygame.mixer.Sound(chemin)
        son.play()

def parler(texte):
    definir_etat("parle")

    try:
        print("🤖 DeskBot :", texte)

        fichier = asyncio.run(
            generer_audio(texte)
        )

        pygame.mixer.music.load(fichier)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.unload()
        os.remove(fichier)

    finally:
        definir_etat("attente")

        # Retour au français après avoir parlé
        from actions.traduction import definir_langue
        definir_langue("fr")



# Test du module
if __name__ == "__main__":

    parler(
        "Bonjour, je suis DeskBot. Je suis prêt."
    )