from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import threading
import os
import logging
import time
from werkzeug.utils import secure_filename
import io
import tempfile
import shutil
from etat_deskbot import obtenir_etat, definir_etat, definir_reponse
from actions.cours import importer_cours
from audio.voix import parler
from cerveau import traiter_commande
from actions.chronometre import chronometre
from actions.minuteur import minuteur
from actions.alarme import obtenir_alarme_principale, prochaine_alarme
from auth import verifier_mot_de_passe, generer_token, token_valide
from actions.temps import lancer_gestionnaire
from actions.mail import lancer_gestionnaire_mails, etat_mails_non_lus, envoyer_mail
from actions.profil_revision import charger_profil, ouvrir_boite_mystere, calculer_rarete_profs
from actions.cours import slugifier
from actions.revision import (generer_questions, session_revision)
from actions.taches import (ajouter_tache, obtenir_taches)
from actions.agenda import obtenir_evenements_mois
from actions.notes import (charger_notes, creer_note, modifier_note, supprimer_note)
from actions.ia import extraire_fichier_avec_gemini
from actions.stl_gcode import convertir_stl_gcode
from actions.compresseur import compresser_fichier, detecter_type
from actions.convertisseur_fichier import convertir_fichier
from actions.images import generer_image
from actions.videos_youtube import (rechercher_videos, obtenir_video, obtenir_recommandations, rechercher_chaines, ajouter_abonnement, supprimer_abonnement, obtenir_abonnements, obtenir_dernieres_videos_abonnements)
from actions.mots_de_passes import generer_mot_de_passe


logging.getLogger("werkzeug").setLevel(logging.ERROR)

app = Flask(__name__)
CORS(app)

lancer_gestionnaire()
lancer_gestionnaire_mails()

definir_etat("connecté")


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

@app.route("/mails/envoyer", methods=["POST"])
def route_envoyer_mail():

    if not acces_autorise():
        return jsonify({"erreur": "Non autorisé"}), 401

    donnees = request.get_json()

    if not donnees:
        return jsonify({
            "erreur": "Données manquantes."
        }), 400

    destinataire = donnees.get("destinataire", "").strip()
    objet = donnees.get("objet", "").strip()
    contenu = donnees.get("contenu", "").strip()

    if not destinataire or not objet or not contenu:
        return jsonify({
            "erreur": "Tous les champs sont obligatoires."
        }), 400

    envoyer_mail(destinataire, objet, contenu)

    return jsonify({
        "message": "Mail envoyé !"
    })

@app.route("/cours/importer", methods=["POST"])
def importer_cours_route():

    print("=== ENVOI MAIL ===")
    print("Authorization :", request.headers.get("Authorization"))
    print("Token local :", request.headers.get("Authorization", "").replace("Bearer ", ""))

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

@app.route("/stl-gcode", methods=["POST"])
def stl_gcode():
    try:
        if "fichier" not in request.files:
            return jsonify({
                "erreur": "Aucun fichier STL envoyé."
            }), 400

        fichier = request.files["fichier"]

        if not fichier.filename:
            return jsonify({
                "erreur": "Aucun fichier sélectionné."
            }), 400

        nom = secure_filename(fichier.filename)

        if not nom.lower().endswith(".stl"):
            return jsonify({
                "erreur": "Le fichier doit être au format .stl"
            }), 400

        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory(
            prefix="deskbot_stl_"
        ) as temp_dir:

            temp_dir = Path(temp_dir)

            stl_temp = temp_dir / nom

            fichier.save(stl_temp)

            contenu_gcode = convertir_stl_gcode(
                stl_temp
            )

            nom_gcode = Path(nom).stem + ".gcode"

            return send_file(
                contenu_gcode,
                mimetype="text/plain",
                headers={
                    "Content-Disposition":
                        f'attachment; filename="{nom_gcode}"'
                }
            )

    except FileNotFoundError as e:
        return jsonify({
            "erreur": str(e)
        }), 500

    except ValueError as e:
        return jsonify({
            "erreur": str(e)
        }), 400

    except RuntimeError as e:
        return jsonify({
            "erreur": str(e)
        }), 500

    except Exception as e:
        print("❌ Erreur STL → G-code :", e)

        return jsonify({
            "erreur":
                "Une erreur est survenue pendant la conversion."
        }), 500

@app.route("/compresser", methods=["POST"])
def compresser():
    try:
        if not acces_autorise():
            return jsonify({
                "succes": False,
                "erreur": "Non autorisé"
            }), 401

        # =========================================================
        # RÉCUPÉRATION DES FICHIERS
        # =========================================================

        fichiers = request.files.getlist("fichiers")

        if not fichiers:
            return jsonify({
                "succes": False,
                "erreur": "Aucun fichier envoyé."
            }), 400

        # Retirer les éventuels champs sans fichier
        fichiers = [
            fichier
            for fichier in fichiers
            if fichier and fichier.filename
        ]

        if not fichiers:
            return jsonify({
                "succes": False,
                "erreur": "Aucun fichier sélectionné."
            }), 400

        # =========================================================
        # IMPORTS
        # =========================================================

        import tempfile
        import zipfile
        from pathlib import Path

        # =========================================================
        # DOSSIER TEMPORAIRE
        # =========================================================

        with tempfile.TemporaryDirectory(
            prefix="deskbot_compresseur_"
        ) as temp_dir:

            temp_dir = Path(temp_dir)

            dossier_entree = temp_dir / "entree"
            dossier_sortie = temp_dir / "sortie"

            dossier_entree.mkdir()
            dossier_sortie.mkdir()

            fichiers_compresses = []

            # =====================================================
            # TRAITEMENT DE CHAQUE FICHIER
            # =====================================================

            for index, fichier in enumerate(fichiers):

                nom = secure_filename(fichier.filename)

                if not nom:
                    continue

                type_fichier = detecter_type(nom)

                if type_fichier is None:
                    return jsonify({
                        "succes": False,
                        "erreur": (
                            f"Format non supporté pour "
                            f"« {fichier.filename} ». "
                            "Formats acceptés : "
                            "JPG, JPEG, PNG, WEBP, BMP, TIFF, "
                            "MP4, MOV, MKV, AVI, WEBM, M4V et PDF."
                        )
                    }), 400

                # -------------------------------------------------
                # Évite les conflits si plusieurs fichiers ont
                # exactement le même nom
                # -------------------------------------------------

                nom_original = Path(nom)

                nom_entree = nom

                if (dossier_entree / nom_entree).exists():
                    nom_entree = (
                        f"{nom_original.stem}_"
                        f"{index + 1}"
                        f"{nom_original.suffix}"
                    )

                fichier_original = dossier_entree / nom_entree

                # -------------------------------------------------
                # Nom du fichier compressé
                # -------------------------------------------------

                fichier_compresse = (
                    dossier_sortie /
                    f"{Path(nom_entree).stem}_compressed"
                    f"{Path(nom_entree).suffix}"
                )

                # -------------------------------------------------
                # Sauvegarde
                # -------------------------------------------------

                fichier.save(fichier_original)

                print(
                    f"📦 Compression : {nom_entree} "
                    f"({type_fichier})"
                )

                # -------------------------------------------------
                # Compression
                # -------------------------------------------------

                resultat = compresser_fichier(
                    fichier_original,
                    fichier_compresse
                )

                print(
                    f"✅ Compression terminée : "
                    f"{resultat['taille_avant']} → "
                    f"{resultat['taille_apres']} octets "
                    f"({resultat['reduction']} %)"
                )

                fichiers_compresses.append({
                    "fichier": fichier_compresse,
                    "nom": fichier_compresse.name,
                    "type": type_fichier,
                    "taille_avant": resultat["taille_avant"],
                    "taille_apres": resultat["taille_apres"],
                    "reduction": resultat["reduction"]
                })

            # =====================================================
            # VÉRIFICATION
            # =====================================================

            if not fichiers_compresses:
                return jsonify({
                    "succes": False,
                    "erreur": "Aucun fichier n'a pu être compressé."
                }), 400

            # =====================================================
            # CRÉATION DU ZIP
            # =====================================================

            zip_path = temp_dir / "fichiers_compresse.zip"

            with zipfile.ZipFile(
                zip_path,
                "w",
                compression=zipfile.ZIP_DEFLATED
            ) as archive:

                for element in fichiers_compresses:

                    archive.write(
                        element["fichier"],
                        arcname=element["nom"]
                    )

            # =====================================================
            # STATISTIQUES
            # =====================================================

            taille_avant_totale = sum(
                element["taille_avant"]
                for element in fichiers_compresses
            )

            taille_apres_totale = sum(
                element["taille_apres"]
                for element in fichiers_compresses
            )

            taille_zip = zip_path.stat().st_size

            if taille_avant_totale > 0:
                reduction_totale = round(
                    (
                        1 -
                        (
                            taille_apres_totale /
                            taille_avant_totale
                        )
                    ) * 100,
                    2
                )
            else:
                reduction_totale = 0

            print(
                f"📦 ZIP créé : "
                f"{len(fichiers_compresses)} fichier(s)"
            )

            print(
                f"📊 Taille avant : "
                f"{taille_avant_totale} octets"
            )

            print(
                f"📊 Taille après compression : "
                f"{taille_apres_totale} octets"
            )

            print(
                f"📦 Taille du ZIP : "
                f"{taille_zip} octets"
            )

            print(
                f"📉 Réduction : "
                f"{reduction_totale} %"
            )

            # =====================================================
            # RETOUR DU ZIP
            # =====================================================

            return send_file(
                zip_path.read_bytes(),
                mimetype="application/zip",
                headers={
                    "Content-Disposition":
                        'attachment; filename="fichiers_compresse.zip"',

                    "X-Nombre-Fichiers":
                        str(len(fichiers_compresses)),

                    "X-Taille-Avant":
                        str(taille_avant_totale),

                    "X-Taille-Apres":
                        str(taille_apres_totale),

                    "X-Taille-Zip":
                        str(taille_zip),

                    "X-Reduction":
                        str(reduction_totale)
                }
            )

    # =============================================================
    # ERREURS
    # =============================================================

    except ValueError as e:

        return jsonify({
            "succes": False,
            "erreur": str(e)
        }), 400

    except RuntimeError as e:

        print(
            "❌ Erreur compresseur :",
            e
        )

        return jsonify({
            "succes": False,
            "erreur": str(e)
        }), 500

    except Exception as e:

        print(
            "❌ Erreur compression :",
            e
        )

        return jsonify({
            "succes": False,
            "erreur": (
                "Une erreur est survenue "
                "pendant la compression."
            )
        }), 500

@app.route("/convertir", methods=["POST"])
def convertir():
    fichier = request.files.get("fichier")
    format_cible = request.form.get("format")

    if not fichier:
        return jsonify({
            "erreur": "Aucun fichier fourni."
        }), 400

    if not fichier.filename:
        return jsonify({
            "erreur": "Le fichier n'a pas de nom."
        }), 400

    if not format_cible:
        return jsonify({
            "erreur": "Aucun format de sortie fourni."
        }), 400

    dossier_temp = tempfile.mkdtemp(
        prefix="deskbot_conversion_"
    )

    try:
        nom_fichier = os.path.basename(
            fichier.filename
        )

        chemin_entree = os.path.join(
            dossier_temp,
            nom_fichier
        )

        fichier.save(chemin_entree)

        extension = format_cible.strip().lower()

        if not extension.startswith("."):
            extension = "." + extension

        nom_sans_extension = os.path.splitext(
            nom_fichier
        )[0]

        chemin_sortie = os.path.join(
            dossier_temp,
            nom_sans_extension + extension
        )

        convertir_fichier(
            chemin_entree,
            extension,
            chemin_sortie
        )

        if not os.path.exists(chemin_sortie):
            raise RuntimeError(
                "Le fichier converti n'a pas été créé."
            )

        reponse = send_file(
            chemin_sortie,
            as_attachment=True,
            download_name=os.path.basename(
                chemin_sortie
            )
        )

        @reponse.call_on_close
        def nettoyer():
            shutil.rmtree(
                dossier_temp,
                ignore_errors=True
            )

        return reponse

    except Exception as e:

        shutil.rmtree(
            dossier_temp,
            ignore_errors=True
        )

        print(
            f"❌ Erreur conversion : {e}"
        )

        return jsonify({
            "erreur": str(e)
        }), 500

# ---------------------------------------------------------
# GÉNÉRATION D'IMAGE
# ---------------------------------------------------------

@app.route("/generer-image", methods=["POST"])
def generer_image_route():

    if not acces_autorise():
        return jsonify({
            "succes": False,
            "erreur": "Non autorisé"
        }), 401

    donnees = request.json or {}

    prompt = donnees.get("prompt", "").strip()
    format_image = donnees.get("format", "1:1")
    qualite = donnees.get("qualite", "moyenne")

    if not prompt:
        return jsonify({
            "succes": False,
            "erreur": "Le prompt est requis."
        }), 400

    try:
        chemin_image = generer_image(
            prompt,
            format_image=format_image,
            qualite=qualite
        )

        if not chemin_image or not os.path.exists(chemin_image):
            return jsonify({
                "succes": False,
                "erreur": "L'image n'a pas été générée."
            }), 500

        reponse = send_file(
            chemin_image,
            mimetype="image/jpeg",
            as_attachment=False,
            download_name="deskbot_image.jpg"
        )

        @reponse.call_on_close
        def nettoyer():
            try:
                if os.path.exists(chemin_image):
                    os.remove(chemin_image)
            except Exception as e:
                print(
                    "⚠️ Impossible de supprimer "
                    "l'image temporaire :", e
                )

        return reponse

    except Exception as e:
        print(
            "❌ Erreur génération image :",
            e
        )

        return jsonify({
            "succes": False,
            "erreur": str(e)
        }), 500

# =========================================================
# YOUTUBE
# =========================================================

@app.get("/youtube/recommandations")
def youtube_recommandations():

    try:

        nombre = request.args.get(
            "nombre",
            40,
            type=int
        )

        videos = obtenir_recommandations(
            nombre
        )

        return jsonify({
            "success": True,
            "videos": videos
        })

    except Exception as e:

        print(
            f"❌ YouTube recommandations : {e}"
        )

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.get("/youtube/abonnements-videos")
def youtube_abonnements_videos():

    try:

        nombre = request.args.get(
            "nombre",
            40,
            type=int
        )

        videos = obtenir_dernieres_videos_abonnements(
            nombre
        )

        return jsonify({
            "success": True,
            "videos": videos
        })

    except Exception as e:

        print(
            f"❌ YouTube abonnements : {e}"
        )

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.get("/youtube/rechercher")
def youtube_rechercher():

    recherche = request.args.get(
        "q",
        "",
        type=str
    )

    if not recherche.strip():

        return jsonify({
            "success": False,
            "error": "Recherche vide."
        }), 400

    try:

        videos = rechercher_videos(
            recherche,
            40
        )

        return jsonify({
            "success": True,
            "videos": videos
        })

    except Exception as e:

        print(f"❌ YouTube recherche : {e}")

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.get("/youtube/video/<video_id>")
def youtube_video(video_id):

    try:

        video = obtenir_video(video_id)

        if not video:

            return jsonify({
                "success": False,
                "error": "Vidéo introuvable."
            }), 404

        return jsonify({
            "success": True,
            "video": video
        })

    except Exception as e:

        print(f"❌ YouTube vidéo : {e}")

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.get("/youtube/chaines")
def youtube_chaines():

    recherche = request.args.get(
        "q",
        "",
        type=str
    )

    if not recherche.strip():

        return jsonify({
            "success": False,
            "error": "Recherche vide."
        }), 400

    try:

        chaines = rechercher_chaines(
            recherche,
            12
        )

        return jsonify({
            "success": True,
            "chaines": chaines
        })

    except Exception as e:

        print(f"❌ YouTube chaînes : {e}")

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.get("/youtube/abonnements")
def youtube_abonnements():

    try:

        return jsonify({
            "success": True,
            "abonnements": obtenir_abonnements()
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.post("/youtube/abonner")
def youtube_abonner():

    donnees = request.get_json(silent=True) or {}

    channel_id = donnees.get("channel_id")
    nom = donnees.get("nom")

    if not channel_id:

        return jsonify({
            "success": False,
            "error": "channel_id manquant."
        }), 400

    success = ajouter_abonnement(
        channel_id,
        nom
    )

    return jsonify({
        "success": success
    })


@app.post("/youtube/desabonner")
def youtube_desabonner():

    donnees = request.get_json(silent=True) or {}

    channel_id = donnees.get("channel_id")

    if not channel_id:

        return jsonify({
            "success": False,
            "error": "channel_id manquant."
        }), 400

    success = supprimer_abonnement(
        channel_id
    )

    return jsonify({
        "success": success
    })

@app.route("/mots-de-passes", methods=["POST"])
def mots_de_passes():
    if not acces_autorise():
        return jsonify({"erreur": "Non autorisé"}), 401

    donnees = request.get_json()
    if not donnees:
        return jsonify({"erreur": "Données manquantes."}), 400

    try:
        longueur = int(donnees.get("longueur", 16))
        
        majuscules = bool(donnees.get("majuscules", True))
        minuscules = bool(donnees.get("minuscules", True))
        chiffres = bool(donnees.get("chiffres", True))
        symboles = bool(donnees.get("symboles", False))
        exclure_ambigus = bool(donnees.get("exclure_ambigus", False))
        
    except (ValueError, TypeError):
        return jsonify({"erreur": "Format des paramètres invalide."}), 400

    try:
        mot_de_passe = generer_mot_de_passe(
            longueur, majuscules, minuscules, chiffres, symboles, exclure_ambigus
        )
    except Exception as e:
        return jsonify({"erreur": f"Erreur de génération : {str(e)}"}), 500

    return jsonify({
        "mot_de_passe": mot_de_passe
    })



def parler_serveur(texte):
    definir_etat("parle")

    try:
        parler(texte)
    finally:
        definir_etat("connecté")

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