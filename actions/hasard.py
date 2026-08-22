import random


def pile_ou_face():
    return random.choice(["pile", "face"])


def lancer_de(faces=6):
    if faces < 2:
        raise ValueError("Un dé doit avoir au moins 2 faces.")

    return random.randint(1, faces)


def nombre_aleatoire(minimum=1, maximum=100):
    if minimum > maximum:
        minimum, maximum = maximum, minimum

    return random.randint(minimum, maximum)


def choix_aleatoire(choix):
    if not choix:
        return None

    return random.choice(choix)


def pourcentage():
    return random.randint(0, 100)


def oui_ou_non():
    return random.choice(["oui", "non"])