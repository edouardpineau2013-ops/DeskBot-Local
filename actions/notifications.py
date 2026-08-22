import requests
from datetime import datetime
from zoneinfo import ZoneInfo


# =========================================================
# CONFIGURATION
# =========================================================

TOPIC_NTFY = "deskbot_notifs"
FUSEAU = ZoneInfo("Europe/Paris")


# =========================================================
# NOTIFICATION IMMEDIATE
# =========================================================

def notifier_telephone(titre, message):
    try:
        response = requests.post(
            f"https://ntfy.sh/{TOPIC_NTFY}",
            data=message.encode("utf-8"),
            headers={
                "Title": titre
            },
            timeout=10
        )

        print(
            f"📱 Notification envoyée | "
            f"HTTP {response.status_code}"
        )

        if not response.ok:
            print("❌ Réponse ntfy :", response.text)

        return response.ok

    except Exception as e:
        print("❌ Erreur notification ntfy :", e)
        return False


# =========================================================
# NOTIFICATION PROGRAMMÉE
# =========================================================

def creer_notification(jour, mois, heure, minute, contenu):

    maintenant = datetime.now(FUSEAU)

    date_notification = datetime(
        maintenant.year,
        mois,
        jour,
        heure,
        minute,
        0,
        tzinfo=FUSEAU
    )

    if date_notification <= maintenant:
        print(
            "⚠️ Notification refusée : "
            "la date est déjà passée."
        )
        return False

    timestamp = int(date_notification.timestamp())

    print(
        f"🔔 Création notification : "
        f"{date_notification.strftime('%d/%m/%Y à %H:%M')}"
    )

    try:

        response = requests.post(
            f"https://ntfy.sh/{TOPIC_NTFY}",
            data=contenu.encode("utf-8"),
            headers={
                "Title": "Notification du DeskBot",
                "At": str(timestamp)
            },
            timeout=10
        )

        print(
            f"📡 ntfy programmation : "
            f"HTTP {response.status_code}"
        )

        if not response.ok:
            print(
                "❌ Erreur ntfy :",
                response.text
            )
            return False

        print(
            "✅ Notification programmée pour",
            date_notification.strftime(
                "%d/%m/%Y à %H:%M"
            )
        )

        return True

    except Exception as e:

        print(
            "❌ Erreur lors de la création "
            "de la notification :",
            e
        )

        return False