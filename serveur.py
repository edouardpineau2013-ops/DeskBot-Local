from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import os
import logging
from werkzeug.utils import secure_filename
from etat_deskbot import obtenir_etat, definir_etat, definir_reponse
from actions.cours import importer_cours
from audio.voix import parler
from cerveau import traiter_commande
from actions.chronometre import chronometre
from actions.minuteur import minuteur
from actions.alarme import obtenir_alarme_principale, prochaine_alarme
from auth import verifier_mot_de_passe, generer_token, token_valide
from actions.temps import lancer_gestionnaire
from actions.mail import lancer_gestionnaire_mails, etat_mails_non_lus
from actions.profil_revision import charger_profil, ouvrir_boite_mystere, calculer_rarete_profs
from actions.cours import slugifier
from actions.revision import (generer_questions, session_revision)
from actions.taches import (ajouter_tache, obtenir_taches)
from actions.agenda import obtenir_evenements_mois
from actions.notes import (charger_notes, creer_note, modifier_note, supprimer_note)
from actions.ia import extraire_fichier_avec_gemini

logging.getLogger("werkzeug").setLevel(logging.ERROR)

app = Flask(__name__)
CORS(app)

lancer_gestionnaire()
lancer_gestionnaire_mails()


@app.route("/")
def accueil():
    return "DeskBot est en ligne !"

@app.route("/etat", methods=["GET"])
def route_etat():
    return jsonify(obtenir_etat())

@app.route("/chronometre")
def afficher_chronometre():
    return jsonify({
        "depart": chronometre.depart,
        "pause_totale": chronometre.pause_totale,
        "en_marche": chronometre.en_marche,
        "en_pause": chronometre.en_pause,
        "temps_pause": chronometre.temps_pause,
        "secondes": chronometre.secondes()
    })

@app.route("/minuteur")
def afficher_minuteur():

    if not acces_autorise():
        return jsonify({"erreur": "Non autorisé"}), 401

    return jsonify({
        "actif": minuteur.actif,
        "en_pause": minuteur.en_pause,
        "secondes": minuteur.temps_restant()
    })

@app.route("/alarme")
def afficher_alarme():

    if not acces_autorise():
        return jsonify({"erreur": "Non autorisé"}), 401

    alarme = obtenir_alarme_principale()

    if alarme is None or "heure" not in alarme or "minute" not in alarme:
        return jsonify({
            "existe": False,
            "heure": None, "minute": None, "active": False, "jours": [],
            "jours_restants": None, "heures_restantes": None, "minutes_restantes": None
        })

    delta = prochaine_alarme()

    if delta is not None:
        jours_restants = delta.days
        heures_restantes = delta.seconds // 3600
        minutes_restantes = (delta.seconds % 3600) // 60
    else:
        jours_restants = heures_restantes = minutes_restantes = None

    return jsonify({
        "existe": True,
        "heure": alarme["heure"],
        "minute": alarme["minute"],
        "active": alarme.get("active", False),
        "jours": alarme.get("jours", []),
        "jours_restants": jours_restants,
        "heures_restantes": heures_restantes,
        "minutes_restantes": minutes_restantes
    })

@app.route("/mails")
def afficher_mails():

    if not acces_autorise():
        return jsonify({"erreur": "Non autorisé"}), 401

    total, details = etat_mails_non_lus()   # ou max_details=50 par exemple

    mails = [
        {
            "expediteur": expediteur,
            "objet": objet
        }
        for expediteur, objet in details
    ]

    return jsonify({
        "non_lus": total,
        "mails": mails
    })

@app.route("/cours/importer", methods=["POST"])
def importer_cours_route():

    if not acces_autorise():
        return jsonify({"erreur": "Non autorisé"}), 401

    matiere = request.form.get("matiere", "").strip()
    chapitre = request.form.get("chapitre", "").strip()
    fichier = request.files.get("fichier")

    if not matiere or not chapitre or fichier is None:
        return jsonify({"erreur": "Matière, chapitre et fichier requis"}), 400

    nom_original = secure_filename(fichier.filename)
    chemin_temp = os.path.join("data", "temp_" + nom_original)
    os.makedirs("data", exist_ok=True)
    fichier.save(chemin_temp)

    try:
        longueur = importer_cours(matiere, chapitre, chemin_temp, nom_original)
    except ValueError as e:
        return jsonify({"erreur": str(e)}), 400
    finally:
        os.remove(chemin_temp)

    return jsonify({"succes": True, "caracteres_extraits": longueur})

@app.route("/revision/profil")
def afficher_profil_revision():

    if not acces_autorise():
        return jsonify({"erreur": "Non autorisé"}), 401

    profil = charger_profil()
    tous_profs = calculer_rarete_profs()

    collection_complete = []
    for prof, infos in tous_profs.items():
        collection_complete.append({
            "nom": prof,
            "slug": slugifier(prof),
            "rarete": infos["rarete"],
            "obtenu": prof in profil["collection"]
        })

    return jsonify({
        "points": profil["points"],
        "serie": profil.get("serie", 0),
        "record_serie": profil.get("record_serie", 0),
        "derniere_revision": profil.get("derniere_revision"),
        "stats_matieres": profil["stats_matieres"],
        "collection": collection_complete
    })


@app.route("/revision/boite", methods=["POST"])
def ouvrir_boite_route():

    if not acces_autorise():
        return jsonify({"erreur": "Non autorisé"}), 401

    return jsonify(ouvrir_boite_mystere())

@app.route("/revision/demarrer", methods=["POST"])
def revision_demarrer():

    if not acces_autorise():
        return jsonify({"erreur": "Non autorisé"}), 401

    matiere = request.json.get("matiere", "").strip()
    chapitre = request.json.get("chapitre", "").strip()

    questions = generer_questions(matiere, chapitre)

    if questions is None:
        return jsonify({
            "succes": False,
            "erreur": "Impossible de générer les questions."
        })

    session_revision.demarrer(questions)

    session_revision.matiere = matiere

    question = session_revision.question_suivante()

    if question is None:
        return jsonify({
            "succes": False,
            "erreur": "Aucune question générée."
        })

    return jsonify({
        "succes": True,
        "question": question,
        "nb_questions": session_revision.nb_total,
        "stats": session_revision.stats()
    })

@app.route("/revision/repondre", methods=["POST"])
def revision_repondre():

    if not acces_autorise():
        return jsonify({"erreur": "Non autorisé"}), 401

    if not session_revision.active:
        return jsonify({
            "erreur": "Aucune révision en cours."
        })

    reponse = request.json.get("reponse", "")

    correcte, explication = session_revision.repondre(reponse)

    question = session_revision.question_suivante()

    if question is None:

        stats = session_revision.stats()

        return jsonify({
            "termine": True,
            "correcte": correcte,
            "explication": explication,
            "stats": stats
        })

    stats = session_revision.stats()

    return jsonify({
        "termine": False,
        "correcte": correcte,
        "explication": explication,
        "question": question,
        "stats": stats
    })

@app.route("/taches", methods=["GET"])
def afficher_taches():

    if not acces_autorise():
        return jsonify({"erreur": "Non autorisé"}), 401

    return jsonify({
        "succes": True,
        "taches": obtenir_taches()
    })

@app.route("/taches", methods=["POST"])
def creer_tache():

    if not acces_autorise():
        return jsonify({"erreur": "Non autorisé"}), 401

    texte = request.json.get("texte", "").strip()

    if not texte:
        return jsonify({
            "succes": False,
            "erreur": "Le texte de la tâche est requis"
        }), 400

    tache = ajouter_tache(texte)

    return jsonify({
        "succes": True,
        "tache": tache
    })

@app.route("/agenda", methods=["GET"])
def agenda():

    try:

        annee = request.args.get("annee", type=int)
        mois = request.args.get("mois", type=int)

        if not annee or not mois:
            return jsonify({
                "succes": False,
                "evenements": []
            }), 400

        evenements = obtenir_evenements_mois(
            annee,
            mois
        )

        return jsonify({
            "succes": True,
            "evenements": evenements
        })

    except Exception as e:

        print("Erreur récupération agenda :", e)

        return jsonify({
            "succes": False,
            "evenements": [],
            "erreur": str(e)
        }), 500

# ---------------------------------------------------------
# NOTES
# ---------------------------------------------------------

@app.route("/notes", methods=["GET"])
def afficher_notes():

    if not acces_autorise():
        return jsonify({"erreur": "Non autorisé"}), 401

    notes = charger_notes()

    return jsonify({
        "succes": True,
        "notes": list(notes.values())
    })


@app.route("/notes", methods=["POST"])
def ajouter_note_route():

    if not acces_autorise():
        return jsonify({"erreur": "Non autorisé"}), 401

    donnees = request.json or {}

    titre = donnees.get("titre", "").strip()
    texte = donnees.get("texte", "").strip()

    if not titre:
        return jsonify({
            "succes": False,
            "erreur": "Le titre de la note est requis."
        }), 400

    resultat = creer_note(titre, texte)

    if "existe déjà" in resultat:
        return jsonify({
            "succes": False,
            "erreur": resultat
        }), 400

    return jsonify({
        "succes": True,
        "message": resultat
    })


@app.route("/notes/<titre>", methods=["PUT"])
def modifier_note_route(titre):

    if not acces_autorise():
        return jsonify({"erreur": "Non autorisé"}), 401

    donnees = request.json or {}

    texte = donnees.get("texte", "")

    resultat = modifier_note(titre, texte)

    if "n'existe pas" in resultat:
        return jsonify({
            "succes": False,
            "erreur": resultat
        }), 404

    return jsonify({
        "succes": True,
        "message": resultat
    })


@app.route("/notes/<titre>", methods=["DELETE"])
def supprimer_note_route(titre):

    if not acces_autorise():
        return jsonify({"erreur": "Non autorisé"}), 401

    resultat = supprimer_note(titre)

    if "n'existe pas" in resultat:
        return jsonify({
            "succes": False,
            "erreur": resultat
        }), 404

    return jsonify({
        "succes": True,
        "message": resultat
    })

# ---------------------------------------------------------
# ANALYSE D'IMAGE / OCR
# ---------------------------------------------------------

@app.route("/analyser-image", methods=["POST"])
def analyser_image_route():

    if not acces_autorise():
        return jsonify({
            "succes": False,
            "erreur": "Non autorisé"
        }), 401

    fichier = request.files.get("image")

    if fichier is None or fichier.filename == "":
        return jsonify({
            "succes": False,
            "erreur": "Aucune image fournie."
        }), 400

    nom_original = secure_filename(fichier.filename)

    if not nom_original:
        return jsonify({
            "succes": False,
            "erreur": "Nom de fichier invalide."
        }), 400

    extensions_autorisees = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp"
    }

    extension = os.path.splitext(nom_original)[1].lower()

    if extension not in extensions_autorisees:
        return jsonify({
            "succes": False,
            "erreur": "Format d'image non supporté. Utilisez JPG, JPEG, PNG ou WEBP."
        }), 400

    mime_type = extensions_autorisees[extension]

    os.makedirs("data", exist_ok=True)

    chemin_temp = os.path.join(
        "data",
        "temp_ocr_" + nom_original
    )

    fichier.save(chemin_temp)

    prompt = """
Analyse cette image et extrais tout le texte visible.

IMPORTANT :
- Recopie exactement le texte présent dans l'image.
- Ne résume pas.
- Ne reformule pas.
- Ne corrige pas les fautes.
- Respecte autant que possible les retours à la ligne.
- Conserve les paragraphes lorsque cela est possible.
- Ne rajoute aucun commentaire.
- Ne mets pas de Markdown.
- Retourne uniquement le texte détecté.
"""

    try:

        texte = extraire_fichier_avec_gemini(
            chemin_temp,
            mime_type,
            prompt
        )

        if texte is None:
            return jsonify({
                "succes": False,
                "erreur": "Impossible d'analyser l'image."
            }), 500

        return jsonify({
            "succes": True,
            "texte": texte
        })

    except Exception as e:

        print("Erreur analyse image :", e)

        return jsonify({
            "succes": False,
            "erreur": "Une erreur est survenue pendant l'analyse de l'image."
        }), 500

    finally:

        if os.path.exists(chemin_temp):
            os.remove(chemin_temp)

def parler_serveur(texte):
    definir_etat("parle")

    try:
        parler(texte)
    finally:
        definir_etat("attente")

@app.route("/commande", methods=["POST"])
def commande():
    if not acces_autorise():
        return jsonify({"erreur": "Non autorisé"}), 401

    texte = request.json["texte"]

    print("Commande :", texte)

    definir_etat("reflexion")

    reponse = traiter_commande(texte)

    definir_reponse(reponse)

    threading.Thread(
        target=parler_serveur,
        args=(reponse,),
        daemon=True
    ).start()

    return jsonify({
        "reponse": reponse
    })

def _token_depuis_requete():
    entete = request.headers.get("Authorization", "")
    if entete.startswith("Bearer "):
        return entete[len("Bearer "):]
    return None

def acces_autorise():
    token = _token_depuis_requete()
    return token is not None and token_valide(token)


@app.route("/login", methods=["POST"])
def login():
    mot_de_passe = request.json.get("mot_de_passe", "")

    if not verifier_mot_de_passe(mot_de_passe):
        return jsonify({"succes": False}), 401

    return jsonify({"succes": True, "token": generer_token()})



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )