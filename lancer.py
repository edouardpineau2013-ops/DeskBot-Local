import subprocess
import time

# Lance le serveur Flask
subprocess.Popen(["python", "serveur.py"])

# Petite pause
time.sleep(2)

# Lance DeskBot
subprocess.Popen(["python", "main.py"])

print("DeskBot lancé.")
print("Ferme cette fenêtre pour arrêter les deux.")

input()