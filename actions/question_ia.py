import os
from groq import Groq
from pydantic import BaseModel, ConfigDict

CLE_GROQ_QUESTIONS = os.environ.get("GROQ_API_KEY_QUESTIONS")

def _demander_a_groq(prompt):
    client = Groq(api_key=CLE_GROQ_QUESTIONS)

    
    reponse = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "Réponds à la question ou la requête reçue."
                    "Réponds exclusivement en français."
                    "Réponds de manière concise et naturelle, car ta réponse sera lue à voix haute. "
                    "Évite les listes longues sauf si elles sont nécessaires."
                    "Évite les caractère spéciaux comme les #, les * et autres sauf si c'est nécessaires."
                    "Ne mets pas de mots en gras ou en italiques, car ça créerait des caractères spéciaux."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]
    )

    return reponse.choices[0].message.content

def generer_reponse_avec_groq(prompt):
    if not CLE_GROQ_QUESTIONS:
        return None

    try:
        return _demander_a_groq(prompt)
    except Exception as e:
        print("Erreur Groq :", e)
        return None