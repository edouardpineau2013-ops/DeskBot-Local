from datetime import datetime


def heure():

    maintenant = datetime.now()

    return (
        f"Il est "
        f"{maintenant.hour} heures "
        f"{maintenant.minute}"
    )