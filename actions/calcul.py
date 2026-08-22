def calculer(texte):

    try:

        expression = (
            texte
            .replace("plus", "+")
            .replace("moins", "-")
            .replace("fois", "*")
            .replace("divisé par", "/")
        )


        resultat = eval(expression)


        return f"Le résultat est {resultat}"


    except:

        return None