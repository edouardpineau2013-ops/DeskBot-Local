import os
from groq import Groq


def corriger_texte(texte):
    if not texte or not texte.strip():
        return "Je n'ai pas trouvé de texte à corriger."

    cle_groq = os.environ.get("GROQ_API_KEY")

    if not cle_groq:
        print("⚠️ CLE_GROQ est introuvable.")
        return "La clé Groq est introuvable."

    try:
        client = Groq(api_key=cle_groq)

        reponse = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un correcteur de français. "
                        "Corrige uniquement les fautes d'orthographe, "
                        "de grammaire, de conjugaison, d'accord, "
                        "de ponctuation et de syntaxe. "
                        "Fais attention au contexte pour choisir entre "
                        "des homophones comme a/à, et/est, ces/ses, "
                        "ce/se, ou/on, son/sont, etc. "
                        "Ne reformule pas inutilement. "
                        "Ne change jamais le sens. "
                        "Ne rajoute aucune explication. "
                        "Retourne uniquement le texte corrigé."
                    )
                },
                {
                    "role": "user",
                    "content": texte
                }
            ],
            temperature=0,
            max_completion_tokens=2048
        )

        texte_corrige = reponse.choices[0].message.content.strip()

        return f"Voilà la version corrigée : {texte_corrige}"

    except Exception as e:
        print(f"⚠️ Erreur correction Groq : {e}")
        return "Je n'ai pas réussi à corriger ce texte."