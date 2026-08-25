from images import generer_image


chemin = generer_image(
    "Un petit robot de bureau futuriste avec un écran OLED, "
    "posé sur un bureau moderne, éclairage cinématique, "
    "rendu 3D réaliste"
)

print("==========================================")
print("       IMAGE GÉNÉRÉE")
print("==========================================")
print()
print("Fichier :", chemin)
print()