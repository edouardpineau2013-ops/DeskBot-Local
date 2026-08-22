import json
import os
import threading

FICHIER_ETAT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data/etat.json"
)

_verrou = threading.Lock()

ETAT_PAR_DEFAUT = "attente"


def definir_etat(etat):
    with _verrou:
        try:
            donnees = {
                "etat": etat,
                "reponse": ""
            }

            # Conserver la réponse existante
            if os.path.exists(FICHIER_ETAT):
                with open(FICHIER_ETAT, "r", encoding="utf-8") as fichier:
                    ancien = json.load(fichier)

                donnees["reponse"] = ancien.get("reponse", "")

            with open(FICHIER_ETAT, "w", encoding="utf-8") as fichier:
                json.dump(
                    donnees,
                    fichier,
                    ensure_ascii=False
                )

        except Exception as e:
            print("Erreur écriture état DeskBot :", e)


def definir_reponse(reponse):
    with _verrou:
        try:
            donnees = {
                "etat": ETAT_PAR_DEFAUT,
                "reponse": reponse
            }

            if os.path.exists(FICHIER_ETAT):
                with open(FICHIER_ETAT, "r", encoding="utf-8") as fichier:
                    ancien = json.load(fichier)

                donnees["etat"] = ancien.get(
                    "etat",
                    ETAT_PAR_DEFAUT
                )

            with open(FICHIER_ETAT, "w", encoding="utf-8") as fichier:
                json.dump(
                    donnees,
                    fichier,
                    ensure_ascii=False
                )

        except Exception as e:
            print("Erreur écriture réponse DeskBot :", e)


def obtenir_etat():
    with _verrou:
        try:
            with open(FICHIER_ETAT, "r", encoding="utf-8") as fichier:
                donnees = json.load(fichier)

            return donnees

        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "etat": ETAT_PAR_DEFAUT,
                "reponse": ""
            }

        except Exception as e:
            print("Erreur lecture état DeskBot :", e)

            return {
                "etat": ETAT_PAR_DEFAUT,
                "reponse": ""
            }