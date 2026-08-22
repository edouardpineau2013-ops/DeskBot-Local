import sounddevice as sd
import webrtcvad
import collections
import wave
import time
import numpy as np
from etat_deskbot import definir_etat


# Configuration audio
SAMPLE_RATE = 16000
CHANNELS = 1

# WebRTC VAD accepte uniquement :
# 8000, 16000, 32000, 48000 Hz
# et des frames de 10, 20 ou 30 ms

FRAME_DURATION = 30  # ms
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION / 1000)


# Niveau de sensibilité
# 0 = peu sensible
# 3 = très sensible
vad = webrtcvad.Vad(3)


def enregistrer_phrase(fichier="commande.wav"):
    definir_etat("ecoute")

    print("🎤 En attente de parole...")

    frames = []

    silence = 0
    parole_detectee = False

    MAX_SILENCE = 20
    # environ 0.6 seconde de silence après la phrase
    
    def callback(indata, frames_count, time_info, status):

        nonlocal silence, parole_detectee

        audio = bytes(indata)

        est_parole = vad.is_speech(
            audio,
            SAMPLE_RATE
        )

        if est_parole:

            frames.append(audio)

            silence = 0
            parole_detectee = True

            print("🗣️", end="", flush=True)

        elif parole_detectee:

            frames.append(audio)

            silence += 1


    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=FRAME_SIZE,
        dtype="int16",
        channels=CHANNELS,
        callback=callback
    ):

        while True:

            time.sleep(0.03)

            if silence > MAX_SILENCE and parole_detectee:
                break


    print("\n✅ Fin de parole")
    definir_etat("reflexion")
    
    # Vérification après l'enregistrement
    if len(frames) < 8:
        print("🔇 Silence détecté")
        return None


    # Sauvegarde WAV

    with wave.open(fichier, "wb") as wf:

        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)

        wf.writeframes(
            b"".join(frames)
        )


    return fichier



# Test seul
if __name__ == "__main__":

    while True:

        fichier = enregistrer_phrase()

        print(
            "Fichier créé :",
            fichier
        )