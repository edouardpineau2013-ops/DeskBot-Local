import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/calendar"]

FICHIER_CREDENTIALS = "credentials_agenda.json"
FICHIER_TOKEN = "token_agenda.json"


def obtenir_service_agenda():
    creds = None

    # =====================================================
    # CHARGEMENT DU TOKEN
    # =====================================================

    if os.path.exists(FICHIER_TOKEN):
        try:
            creds = Credentials.from_authorized_user_file(
                FICHIER_TOKEN,
                SCOPES
            )
        except Exception as e:
            print(f"⚠️ Impossible de charger le token Agenda : {e}")
            creds = None

    # =====================================================
    # RENOUVELLEMENT DU TOKEN
    # =====================================================

    if creds and creds.expired and creds.refresh_token:

        try:
            creds.refresh(Request())

        except Exception as e:

            print(
                f"⚠️ Impossible de renouveler le token Agenda : {e}"
            )

            # Le refresh token est probablement révoqué
            creds = None

            try:
                os.remove(FICHIER_TOKEN)
                print("🗑️ Ancien token Agenda supprimé.")
            except OSError:
                pass

    # =====================================================
    # NOUVELLE AUTHENTIFICATION
    # =====================================================

    if not creds or not creds.valid:

        print("🔐 Nouvelle authentification Google Agenda...")

        flow = InstalledAppFlow.from_client_secrets_file(
            FICHIER_CREDENTIALS,
            SCOPES
        )

        creds = flow.run_local_server(
            port=0,
            access_type="offline",
            prompt="consent"
        )

    # =====================================================
    # SAUVEGARDE
    # =====================================================

    with open(FICHIER_TOKEN, "w") as token:
        token.write(creds.to_json())

    return build(
        "calendar",
        "v3",
        credentials=creds
    )


# ============================================================
# AJOUTER UN ÉVÉNEMENT
# ============================================================

def ajouter_evenement(
    titre,
    date,
    heure_debut,
    duree_minutes=60,
    description=None,
    lieu=None
):

    service = obtenir_service_agenda()

    fuseau = ZoneInfo("Europe/Paris")

    debut = datetime.strptime(
        f"{date} {heure_debut}",
        "%Y-%m-%d %H:%M"
    ).replace(tzinfo=fuseau)

    fin = debut + timedelta(minutes=duree_minutes)

    evenement = {
        "summary": titre,
        "start": {
            "dateTime": debut.isoformat(),
            "timeZone": "Europe/Paris"
        },
        "end": {
            "dateTime": fin.isoformat(),
            "timeZone": "Europe/Paris"
        }
    }

    if description:
        evenement["description"] = description

    if lieu:
        evenement["location"] = lieu

    resultat = service.events().insert(
        calendarId="primary",
        body=evenement
    ).execute()

    return resultat


# ============================================================
# OBTENIR LES ÉVÉNEMENTS
# ============================================================

def obtenir_evenements(
    date=None,
    nombre_max=20
):
    """
    Récupère les événements d'une journée.

    date :
        "2026-08-15"

    Si date=None :
        récupère les prochains événements.
    """

    service = obtenir_service_agenda()

    if date:
        debut_journee = datetime.strptime(
            date,
            "%Y-%m-%d"
        )

        fin_journee = debut_journee + timedelta(days=1)

        time_min = debut_journee.isoformat() + "+02:00"
        time_max = fin_journee.isoformat() + "+02:00"

        resultat = service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            maxResults=nombre_max,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

    else:
        maintenant = datetime.now().astimezone()

        resultat = service.events().list(
            calendarId="primary",
            timeMin=maintenant.isoformat(),
            maxResults=nombre_max,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

    return resultat.get("items", [])



def obtenir_evenements_mois(annee, mois):
    service = obtenir_service_agenda()

    debut = datetime(
        annee,
        mois,
        1,
        tzinfo=ZoneInfo("Europe/Paris")
    )

    if mois == 12:
        fin = datetime(
            annee + 1,
            1,
            1,
            tzinfo=ZoneInfo("Europe/Paris")
        )
    else:
        fin = datetime(
            annee,
            mois + 1,
            1,
            tzinfo=ZoneInfo("Europe/Paris")
        )

    resultat = service.events().list(
        calendarId="primary",
        timeMin=debut.isoformat(),
        timeMax=fin.isoformat(),
        maxResults=250,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    evenements = []

    for evenement in resultat.get("items", []):

        debut_evenement = evenement.get("start", {})

        if "dateTime" in debut_evenement:

            date_heure = datetime.fromisoformat(
                debut_evenement["dateTime"].replace("Z", "+00:00")
            )

            date = date_heure.astimezone(
                ZoneInfo("Europe/Paris")
            ).strftime("%Y-%m-%d")

            heure = date_heure.astimezone(
                ZoneInfo("Europe/Paris")
            ).strftime("%H:%M")

        elif "date" in debut_evenement:

            date = debut_evenement["date"]
            heure = None

        else:
            continue

        evenements.append({
            "id": evenement.get("id"),
            "titre": evenement.get(
                "summary",
                "Événement sans titre"
            ),
            "date": date,
            "heure": heure
        })

    return evenements


# ============================================================
# PROCHAINS ÉVÉNEMENTS
# ============================================================

def prochains_evenements(nombre=5):
    """
    Retourne les prochains événements de l'agenda.
    """

    return obtenir_evenements(
        date=None,
        nombre_max=nombre
    )


# ============================================================
# RECHERCHER UN ÉVÉNEMENT
# ============================================================

def rechercher_evenement(texte, nombre_max=10):
    """
    Recherche un événement contenant un texte dans son titre.
    """

    service = obtenir_service_agenda()

    maintenant = datetime.now().astimezone()

    resultat = service.events().list(
        calendarId="primary",
        timeMin=maintenant.isoformat(),
        q=texte,
        maxResults=nombre_max,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    return resultat.get("items", [])


# ============================================================
# SUPPRIMER UN ÉVÉNEMENT
# ============================================================

def supprimer_evenement(event_id):
    """
    Supprime un événement grâce à son ID Google Calendar.
    """

    service = obtenir_service_agenda()

    service.events().delete(
        calendarId="primary",
        eventId=event_id
    ).execute()

    return True


# ============================================================
# MODIFIER UN ÉVÉNEMENT
# ============================================================

def modifier_evenement(
    event_id,
    titre=None,
    date=None,
    heure_debut=None,
    duree_minutes=None,
    description=None,
    lieu=None
):
    """
    Modifie un événement existant.

    Seuls les paramètres fournis sont modifiés.
    """

    service = obtenir_service_agenda()

    evenement = service.events().get(
        calendarId="primary",
        eventId=event_id
    ).execute()

    if titre is not None:
        evenement["summary"] = titre

    if description is not None:
        evenement["description"] = description

    if lieu is not None:
        evenement["location"] = lieu

    if date is not None and heure_debut is not None:

        debut = datetime.strptime(
            f"{date} {heure_debut}",
            "%Y-%m-%d %H:%M"
        ).replace(
            tzinfo=ZoneInfo("Europe/Paris")
        )

        if duree_minutes is None:
            ancienne_date = evenement["start"].get("dateTime")

            if ancienne_date:
                ancienne_date = datetime.fromisoformat(
                    ancienne_date.replace("Z", "+00:00")
                )

                ancienne_fin = evenement["end"].get("dateTime")

                if ancienne_fin:
                    ancienne_fin = datetime.fromisoformat(
                        ancienne_fin.replace("Z", "+00:00")
                    )

                    duree_minutes = int(
                        (ancienne_fin - ancienne_date).total_seconds()
                        / 60
                    )

        if duree_minutes is None:
            duree_minutes = 60

        fin = debut + timedelta(minutes=duree_minutes)

        evenement["start"] = {
            "dateTime": debut.isoformat(),
            "timeZone": "Europe/Paris"
        }

        evenement["end"] = {
            "dateTime": fin.isoformat(),
            "timeZone": "Europe/Paris"
        }

    resultat = service.events().update(
        calendarId="primary",
        eventId=event_id,
        body=evenement
    ).execute()

    return resultat


# ============================================================
# FORMATER UN ÉVÉNEMENT POUR DESKBOT
# ============================================================

def formater_evenement(evenement):
    """
    Transforme un événement Google en texte simple.
    """

    titre = evenement.get(
        "summary",
        "Événement sans titre"
    )

    debut = evenement.get("start", {})

    if "dateTime" in debut:
        date_heure = datetime.fromisoformat(
            debut["dateTime"].replace("Z", "+00:00")
        )

        date = date_heure.strftime("%d/%m/%Y")
        heure = date_heure.strftime("%H:%M")

        texte = f"{titre} le {date} à {heure}"

    else:
        date = debut.get("date", "")
        texte = f"{titre} le {date}"

    return texte