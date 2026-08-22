from faster_whisper import WhisperModel
import unicodedata
import re

print("Chargement du modèle Whisper...")

model = WhisperModel(
    "base",          # tiny, base, small, medium, large
    device="cpu",
    compute_type="int8"
)

print("Whisper prêt !")


# =========================================================
# PROMPT DE CONTEXTE : ABANDONNÉ
#
# Une tentative de biaiser la reconnaissance avec un
# initial_prompt (mots-clés + noms de villes rares) a été
# testée, mais elle a révélé un problème plus grave que celui
# qu'elle tentait de résoudre : sur un audio court ou peu
# clair, faster-whisper peut "s'effondrer" et recopier
# littéralement le texte du prompt comme s'il s'agissait de
# la transcription (observé : "salut" transcrit en "il peut
# aussi mentionner ces villes", extrait exact du prompt).
#
# C'est un comportement documenté de Whisper avec
# initial_prompt sur les petits modèles et les énoncés courts,
# pas quelque chose de réglable en ajustant la longueur ou le
# contenu du prompt. Le risque (des commandes entières
# remplacées par du texte du prompt) dépasse largement le
# bénéfice (meilleure reconnaissance de quelques noms de
# villes rares). On revient donc à une transcription sans
# biais de contexte.
#
# Si un nom de ville rare (Fontvieille, etc.) est mal
# transcrit, c'est maintenant le rattrapage par fuzzy matching
# dans commandes.py (_ville_apres_a) qui prend le relais.
# =========================================================


def nettoyer_texte(texte):
    # Minuscules
    texte = texte.lower()

    # Suppression des accents
    texte = unicodedata.normalize("NFD", texte)
    texte = "".join(
        c for c in texte
        if unicodedata.category(c) != "Mn"
    )

    # Suppression de la ponctuation
    texte = re.sub(r"[^\w\s]", "", texte)

    # Suppression des espaces multiples
    texte = re.sub(r"\s+", " ", texte)

    return texte.strip()


def reconnaitre(fichier):

    segments, info = model.transcribe(
        fichier,
        language="fr",
        beam_size=10,
        best_of=5,
        temperature=0.0,
        vad_filter=True,
        vad_parameters=dict(
            min_silence_duration_ms=300
        )
    )

    texte = ""

    for segment in segments:
        texte += segment.text + " "

    texte = nettoyer_texte(texte)

    print(f"📝 ({info.language} - {round(info.language_probability*100)}%) : {texte}")

    return texte