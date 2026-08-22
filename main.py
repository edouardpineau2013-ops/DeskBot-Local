from audio.ecoute import enregistrer_phrase
from audio.voix import parler

from ia.whisper import reconnaitre

from commandes import trouver_commande
from cerveau import traiter_commande
from actions.temps import lancer_gestionnaire
from actions.mail import lancer_gestionnaire_mails
from etat_deskbot import definir_etat, definir_reponse

print("🤖 Initialisation DeskBot...")
lancer_gestionnaire()
lancer_gestionnaire_mails()

actif = False

def parler_avec_etat(texte):
    definir_etat("parle")

    try:
        parler(texte)
    finally:
        definir_etat("attente")

parler_avec_etat("Bonjour. Je suis DeskBot. Dites 'DeskBot activé' pour m'activer.")

while True:
    try:

        definir_etat("ecoute")

        fichier = enregistrer_phrase()

        if fichier is None:
            definir_etat("attente")
            continue

        definir_etat("reflexion")

        texte = reconnaitre(fichier)

        texte = texte.strip().lower()

        if len(texte) < 4:
            print("🔇 Bruit ignoré")
            continue

        print("👤", texte)

        commande = trouver_commande(texte)

        print("Commande reconnue :", commande)

        # -----------------------
        # MODE VEILLE
        # -----------------------

        if not actif:

            if commande == "activation":

                actif = True

                parler_avec_etat("DeskBot activé. Je vous écoute.")

            else:

                print("😴 En veille...")

            continue

        # -----------------------
        # DÉSACTIVATION
        # -----------------------

        if commande == "desactivation":

            actif = False

            parler_avec_etat("DeskBot désactivé.")

            continue

        # -----------------------
        # TRAITEMENT
        # -----------------------

        definir_etat("reflexion")

        reponse = traiter_commande(texte)

        definir_reponse(reponse)

        parler_avec_etat(reponse)

        if commande == "au_revoir":
            break

    except KeyboardInterrupt:

        break

    except Exception as e:

        print(e)