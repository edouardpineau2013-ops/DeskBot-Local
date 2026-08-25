import asyncio
import os
import tempfile
import uuid

import edge_tts

from etat_deskbot import definir_etat
from actions.traduction import retourner_langue


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


def _obtenir_pygame():

    try:
        import pygame

        return pygame

    except ImportError:

        print(
            "🔊 pygame n'est pas disponible. "
            "La lecture audio est désactivée."
        )

        return None


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


def jouer_son(chemin):

    pygame = _obtenir_pygame()

    if pygame is None:
        return False

    try:

        pygame.mixer.init()

        son = pygame.mixer.Sound(chemin)
        son.play()

        return True

    except Exception as e:

        print("🔊 Impossible de jouer le son :", e)

        return False


def parler(texte):

    definir_etat("parle")

    fichier = None

    try:

        print("🤖 DeskBot :", texte)

        pygame = _obtenir_pygame()

        # Sur Render :
        # on peut générer la voix, mais il n'y a
        # aucun haut-parleur à utiliser.
        if pygame is None:
            return False

        fichier = asyncio.run(
            generer_audio(texte)
        )

        pygame.mixer.init()

        pygame.mixer.music.load(fichier)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():

            pygame.time.Clock().tick(10)

        pygame.mixer.music.unload()

        return True

    except Exception as e:

        print("🗣️ Erreur audio :", e)

        return False

    finally:

        definir_etat("connecté")

        if fichier and os.path.exists(fichier):

            try:
                os.remove(fichier)

            except Exception:
                pass

        # Retour au français après avoir parlé
        try:

            from actions.traduction import definir_langue

            definir_langue("fr")

        except Exception:
            pass


# Compatibilité avec les anciens imports
# --------------------------------------------------
# notifier_telephone est désormais dans
# actions.notifications.py.
#
# On le réexporte ici afin que les anciens fichiers
# qui utilisent :
#
# from audio.voix import notifier_telephone
#
# continuent de fonctionner.
# --------------------------------------------------

from actions.notifications import notifier_telephone


if __name__ == "__main__":

    parler(
        "Bonjour, je suis DeskBot. Je suis prêt."
    )