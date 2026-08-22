import time
from chronometre import chronometre

chronometre.demarrer()

while True:
    print(chronometre.texte(), end="\r")
    time.sleep(1)