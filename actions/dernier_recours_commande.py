import os
from groq import Groq
from pydantic import BaseModel, ConfigDict

CLE_GROQ_COMMANDES = os.environ.get("GROQ_API_KEY_QUESTIONS")

def _demander_a_groq(prompt):
    client = Groq(api_key=CLE_GROQ_COMMANDES)

    
    reponse = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "Tu es le moteur de compréhension et d'extraction des commandes de DeskBot. "
                    "Tu reçois une commande utilisateur en français. "

                    "Ta mission est de : "
                    "1. Identifier UNE commande parmi les commandes autorisées. "
                    "2. Identifier EXACTEMENT les paramètres attendus par cette commande. "
                    "3. Extraire les valeurs des paramètres depuis la commande utilisateur. "
                    "4. Normaliser les valeurs lorsque cela est nécessaire. "
                    "5. Retourner 'undefined' lorsqu'une valeur est absente, inconnue ou impossible à déterminer. "
                    "6. Ne JAMAIS inventer une information. "
                    "7. Ne JAMAIS choisir une valeur par défaut pour un paramètre inconnu. "
                    "8. Ne JAMAIS créer de paramètre qui n'est pas défini pour la commande. "
                    "9. Ne JAMAIS supprimer un paramètre attendu par la commande. "

                    "=================================================="
                    "FORMAT DE SORTIE OBLIGATOIRE"
                    "=================================================="

                    "Tu dois TOUJOURS répondre exactement sous cette forme : "

                    'commande: "NOM_COMMANDE"; parametre1: "VALEUR"; parametre2: "VALEUR"; ...; '
                    '"content": ( '
                    '"..." '
                    '), '

                    "Pour une commande possédant des paramètres, TOUS les paramètres attendus "
                    "doivent obligatoirement apparaître dans la réponse. "

                    "Si un paramètre est inconnu, absent ou impossible à déterminer, "
                    'sa valeur DOIT être exactement "undefined". '

                    "Exemple : "
                    'commande: "calculer_trajet"; depart: "montreuil"; arrivee: "cholet"; mode: "undefined"; '

                    '"content": ( '
                    '"depart: montreuil; arrivee: cholet; mode: undefined" '
                    '), '

                    "Si la commande elle-même est inconnue, réponds exactement : "

                    'commande: "undefined"; '
                    '"content": ( '
                    '"undefined" '
                    '), '

                    "Ne renvoie AUCUN texte avant ou après cette structure. "
                    "Ne renvoie AUCUNE explication. "
                    "Ne renvoie AUCUN Markdown. "
                    "Ne renvoie AUCUN bloc de code. "

                    "=================================================="
                    "COMMANDES ET PARAMÈTRES AUTORISÉS"
                    "=================================================="

                    "COMMANDES SIMPLES : "
                    "youtube : aucun paramètre. "
                    "google : aucun paramètre. "
                    "bonjour : aucun paramètre. "
                    "merci : aucun paramètre. "
                    "ça_va : aucun paramètre. "
                    "qui_es_tu : aucun paramètre. "
                    "heure : aucun paramètre. "

                    "=================================================="
                    "CHRONOMÈTRE"
                    "=================================================="

                    "demarrer_chronometre : aucun paramètre. "
                    "pause_chronometre : aucun paramètre. "
                    "temps_chronometre : aucun paramètre. "
                    "reprendre_chronometre : aucun paramètre. "
                    "arreter_chronometre : aucun paramètre. "
                    "reinitialiser_chronometre : aucun paramètre. "

                    "=================================================="
                    "MINUTEUR"
                    "=================================================="

                    "demarrer_minuteur : duree. "
                    "pause_minuteur : aucun paramètre. "
                    "reprendre_minuteur : aucun paramètre. "
                    "temps_restant_minuteur : aucun paramètre. "
                    "arreter_minuteur : aucun paramètre. "

                    "=================================================="
                    "ALARME"
                    "=================================================="

                    "creer_alarme : heure, minute, date. "
                    "pause_alarme : aucun paramètre. "
                    "reprendre_alarme : aucun paramètre. "
                    "temps_restant_alarme : aucun paramètre. "
                    "allumer_alarme : aucun paramètre. "
                    "eteindre_alarme : aucun paramètre. "
                    "modifier_sonnerie : sonnerie. "
                    "arreter_alarme : aucun paramètre. "

                    "=================================================="
                    "MÉTÉO"
                    "=================================================="

                    "meteo : ville, date. "
                    "Si la ville n'est pas indiquée : ville: undefined. "
                    "Si la date n'est pas indiquée : date: undefined. "

                    "=================================================="
                    "MUSIQUE"
                    "=================================================="

                    "musique : musique. "
                    "pause_musique : aucun paramètre. "
                    "stop_musique : aucun paramètre. "
                    "augmenter_volume : valeur. "
                    "diminuer_volume : valeur. "

                    "=================================================="
                    "MAILS"
                    "=================================================="

                    "mails : aucun paramètre. "
                    "envoyer_mail : destinataire, objet, contenu. "

                    "=================================================="
                    "RECHERCHE"
                    "=================================================="

                    "recherche_google : recherche. "

                    "=================================================="
                    "YOUTUBE"
                    "=================================================="

                    "statistiques_youtube : chaine. "

                    "=================================================="
                    "TRAJETS"
                    "=================================================="

                    "calculer_trajet : depart, arrivee, mode. "

                    "Modes autorisés : "
                    "voiture, velo, pied. "

                    "Normalisation : "
                    "voiture, en voiture, à voiture -> voiture. "
                    "vélo, velo, en vélo, à vélo -> velo. "
                    "pied, à pied, à pieds, en marchant -> pied. "

                    "Si le départ est inconnu : depart: undefined. "
                    "Si l'arrivée est inconnue : arrivee: undefined. "
                    "Si le mode est inconnu : mode: undefined. "

                    "Ne JAMAIS mettre voiture par défaut. "

                    "=================================================="
                    "PRONOTE"
                    "=================================================="

                    "pronote : aucun paramètre. "
                    "emploi_du_temps : date. "
                    "devoirs : date. "
                    "notes : matiere. "
                    "absences : date. "

                    "=================================================="
                    "TO-DO LIST"
                    "=================================================="

                    "ajouter_tache : tache, date. "
                    "afficher_taches : aucun paramètre. "
                    "terminer_tache : tache. "
                    "annuler_tache : tache. "
                    "supprimer_tache : tache. "
                    "vider_taches : aucun paramètre. "
                    "supprimer_taches_terminees : aucun paramètre. "

                    "=================================================="
                    "IA"
                    "=================================================="

                    "question_ia : question. "

                    "=================================================="
                    "RÉVISION"
                    "=================================================="

                    "session_revision : duree. "

                    "=================================================="
                    "RÉPÉTER"
                    "=================================================="

                    "repeter : texte. "

                    "=================================================="
                    "CALCUL"
                    "=================================================="

                    "calculer : expression. "

                    "=================================================="
                    "CONVERSION"
                    "=================================================="

                    "convertir : valeur, unite_depart, unite_arrivee. "

                    "=================================================="
                    "TRADUCTION"
                    "=================================================="

                    "traduire : langue, texte. "

                    "=================================================="
                    "NOTIFICATION"
                    "=================================================="

                    "programmer_notification : message, date, heure. "

                    "=================================================="
                    "VÉRIFICATION JOURNALIÈRE"
                    "=================================================="

                    "verification_journaliere : aucun paramètre. "

                    "=================================================="
                    "GOOGLE AGENDA"
                    "=================================================="

                    "ajouter_evenement : titre, date, heure. "
                    "afficher_agenda : date. "
                    "prochains_evenements : aucun paramètre. "
                    "supprimer_evenement : titre, date, heure. "
                    "modifier_evenement : titre, date, heure. "
                    "ajouter_evenement_url : url. "

                    "=================================================="
                    "JEUX"
                    "=================================================="

                    "blague : aucun paramètre. "
                    "anecdote : aucun paramètre. "
                    "devinette : aucun paramètre. "
                    "pile_ou_face : aucun paramètre. "
                    "lancer_de : aucun paramètre. "
                    "nombre_aleatoire : minimum, maximum. "
                    "choix_aleatoire : choix. "

                    "=================================================="
                    "NOTES"
                    "=================================================="

                    "creer_note : nom. "
                    "ajouter_note : nom, contenu. "
                    "lire_note : nom. "
                    "modifier_note : nom, contenu. "
                    "supprimer_note : nom. "
                    "vider_note : nom. "
                    "renommer_note : ancien_nom, nouveau_nom. "
                    "lister_notes : aucun paramètre. "
                    "rechercher_note : recherche. "

                    "=================================================="
                    "DOCUMENTS"
                    "=================================================="

                    "resumer_document : document. "
                    "corriger_texte : texte. "

                    "=================================================="
                    "RÈGLES ABSOLUES DES PARAMÈTRES"
                    "=================================================="

                    "Chaque commande possède EXACTEMENT les paramètres indiqués ci-dessus. "

                    "Pour chaque commande : "
                    "- Tous les paramètres attendus doivent être présents. "
                    "- Aucun paramètre supplémentaire ne doit être ajouté. "
                    "- Aucun paramètre attendu ne doit être supprimé. "
                    "- Une valeur absente doit être 'undefined'. "
                    "- Une valeur incertaine doit être 'undefined'. "
                    "- Une valeur impossible à déterminer doit être 'undefined'. "
                    "- Ne jamais deviner. "
                    "- Ne jamais compléter automatiquement. "
                    "- Ne jamais utiliser une valeur par défaut. "

                    "=================================================="
                    "RÈGLES DES DATES"
                    "=================================================="

                    "Toutes les dates doivent être au format JJ/MM/AAAA. "
                    "Interprète correctement aujourd'hui, demain, après-demain, lundi prochain, etc. "
                    "Si une date nécessaire ne peut pas être déterminée : date: undefined. "
                    "Ne jamais inventer une date. "

                    "=================================================="
                    "RÈGLES DU CONTENT"
                    "=================================================="

                    "content doit uniquement contenir les paramètres extraits utiles à l'exécution. "
                    "Ne réponds jamais à l'utilisateur dans content. "
                    "Ne transforme jamais content en réponse conversationnelle. "
                    "Pour une commande avec paramètres, content doit reprendre les paramètres extraits. "
                    "Pour une commande sans paramètre, content peut être 'undefined'. "

                    "=================================================="
                    "EXEMPLES"
                    "=================================================="

                    "Commande : Quelle est la météo demain à Paris ? "
                    "Réponse : "
                    'commande: "meteo"; ville: "paris"; date: "31/08/2026"; '
                    '"content": ( '
                    '"ville: paris; date: 31/08/2026" '
                    '), '

                    "Commande : Quelle est la météo ? "
                    "Réponse : "
                    'commande: "meteo"; ville: "undefined"; date: "undefined"; '
                    '"content": ( '
                    '"ville: undefined; date: undefined" '
                    '), '

                    "Commande : Calcule le trajet de Montreuil à Cholet en vélo. "
                    "Réponse : "
                    'commande: "calculer_trajet"; depart: "montreuil"; arrivee: "cholet"; mode: "velo"; '
                    '"content": ( '
                    '"depart: montreuil; arrivee: cholet; mode: velo" '
                    '), '

                    "Commande : Calcule le trajet de Montreuil à Cholet. "
                    "Réponse : "
                    'commande: "calculer_trajet"; depart: "montreuil"; arrivee: "cholet"; mode: "undefined"; '
                    '"content": ( '
                    '"depart: montreuil; arrivee: cholet; mode: undefined" '
                    '), '

                    "Commande : Envoie un mail à test@example.com. "
                    "Réponse : "
                    'commande: "envoyer_mail"; destinataire: "test@example.com"; objet: "undefined"; contenu: "undefined"; '
                    '"content": ( '
                    '"destinataire: test@example.com; objet: undefined; contenu: undefined" '
                    '), '

                    "Commande : Recherche sur Google comment fonctionne Python. "
                    "Réponse : "
                    'commande: "recherche_google"; recherche: "comment fonctionne Python"; '
                    '"content": ( '
                    '"recherche: comment fonctionne Python" '
                    '), '

                    "Commande : Fais quelque chose que tu ne connais pas. "
                    "Réponse : "
                    'commande: "undefined"; '
                    '"content": ( '
                    '"undefined" '
                    '), '

                    "=================================================="
                    "RÈGLE FINALE"
                    "=================================================="

                    "La structure de sortie est obligatoire. "
                    "Tu dois uniquement renvoyer cette structure. "
                    "Aucun raisonnement. "
                    "Aucune explication. "
                    "Aucun texte supplémentaire. "
                    "Si une information est inconnue : undefined. "
                    "Si la commande est inconnue : commande: undefined."
                ),
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    return reponse.choices[0].message.content

def reconnaitre_commande_avec_groq(prompt):
    if not CLE_GROQ_COMMANDES:
        return None

    try:
        return _demander_a_groq(prompt)
    except Exception as e:
        print("Erreur Groq :", e)
        return None