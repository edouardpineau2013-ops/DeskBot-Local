import os
from google import genai
from groq import Groq

CLES_GEMINI = [
    os.environ.get("GEMINI_API_KEY"),
    os.environ.get("GEMINI_API_KEY_2"),
]
CLE_GROQ = os.environ.get("GROQ_API_KEY")


def _est_erreur_quota(exception):
    texte = str(exception).lower()
    return any(mot in texte for mot in ["429", "quota", "resource_exhausted", "rate limit", "rate_limit"])

def _appeler_groq(prompt, schema_pydantic):
    client = Groq(api_key=CLE_GROQ)

    
    reponse = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "IMPORTANT : "
                    "- Réponds exclusivement en français."
                    "- Les questions doivent être en français."
                    "- Les réponses doivent être en français."
                    "- Les explications doivent être en français."
                    "- Ne réponds jamais en anglais, sauf lorsqu'il s'agit d'un cours de langue étrangère."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": schema_pydantic.__name__,
                "schema": schema_pydantic.model_json_schema(),
                "strict": True
            }
        }
    )

    return schema_pydantic.model_validate_json(reponse.choices[0].message.content)

def generer_avec_groq(prompt, schema_pydantic):
    if not CLE_GROQ:
        return None

    try:
        return _appeler_groq(prompt, schema_pydantic)
    except Exception as e:
        print("Erreur Groq :", e)
        return None

def _resumer_avec_groq(texte):
    client = Groq(api_key=CLE_GROQ)

    reponse = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "Résume ce texte en français. "
                    "Fais des phrases claires et pas trop longues. "
                    "Analyse le sujet, retiens les points clés et résume-les clairement. "
                    "Ne mets pas de petits commentaires : juste le résumé."
                    "Ne mets pas de mots en gras, en italique ou autre style. Ta réponse sera lue à l'oral."
                ),
            },
            {
                "role": "user",
                "content": texte,
            },
        ],
    )

    return reponse.choices[0].message.content


def resumer_avec_groq(texte):
    if not CLE_GROQ:
        return None

    try:
        return _resumer_avec_groq(texte)
    except Exception as e:
        print("Erreur Groq :", e)
        return None

def analyser_image(chemin_image, mime_type):
    prompt = """
Analyse cette image et extrais tout le texte visible.

IMPORTANT :
- Recopie exactement le texte présent dans l'image.
- Ne résume pas.
- Ne reformule pas.
- Ne corrige pas les fautes.
- Respecte les retours à la ligne autant que possible.
- Ne rajoute aucun commentaire.
- Si l'image ne contient aucun texte, indique simplement qu'aucun texte n'a été détecté.
"""

    return extraire_fichier_avec_gemini(
        chemin_image,
        mime_type,
        prompt
    )

def extraire_fichier_avec_gemini(chemin_fichier, mime_type, prompt):
    """Extrait le texte d'un document avec Gemini (clé 1 puis clé 2)."""

    type_contenu = "document" if mime_type == "application/pdf" else "image"

    for i, cle in enumerate(CLES_GEMINI):
        if not cle:
            continue
        try:
            client = genai.Client(api_key=cle)
            fichier = client.files.upload(file=chemin_fichier)

            interaction = client.interactions.create(
                model="gemini-3.5-flash",
                input=[
                    {"type": "text", "text": prompt},
                    {"type": type_contenu, "uri": fichier.uri, "mime_type": mime_type}
                ]
            )
            return interaction.output_text
        except Exception as e:
            raison = "quota épuisé" if _est_erreur_quota(e) else f"erreur ({e})"
            print(f"Gemini clé {i + 1} indisponible ({raison}), bascule...")
            continue

    return None