import secrets
import string

def generer_mot_de_passe(
    longueur=16,
    majuscules=True,
    minuscules=True,
    chiffres=True,
    symboles=True,
    exclure_ambigus=False
):
    caracteres = ""

    if majuscules:
        caracteres += string.ascii_uppercase

    if minuscules:
        caracteres += string.ascii_lowercase

    if chiffres:
        caracteres += string.digits

    if symboles:
        caracteres += "!@#$%^&*()-_=+[]{};:,.?/"

    if exclure_ambigus:
        caracteres = caracteres.translate(
            str.maketrans("", "", "O0Il1")
        )

    if not caracteres:
        raise ValueError("Aucun type de caractère sélectionné.")

    return "".join(
        secrets.choice(caracteres)
        for _ in range(longueur)
    )