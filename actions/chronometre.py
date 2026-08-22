import time

class Chronometre:

    def __init__(self):

        self.depart = None
        self.temps_pause = None
        self.pause_totale = 0

        self.en_marche = False
        self.en_pause = False
        self.secondes_figees = 0


    def demarrer(self):

        if self.en_marche:
            return False

        self.depart = time.time()
        self.pause_totale = 0
        self.en_marche = True
        self.en_pause = False

        return True
    


    def pause(self):

        if not self.en_marche:
            return False

        if self.en_pause:
            return False

        self.temps_pause = time.time()
        self.en_pause = True

        return True


    def reprendre(self):

        if not self.en_pause:
            return False

        self.pause_totale += time.time() - self.temps_pause

        self.en_pause = False

        return True


    def arreter(self):

        if not self.en_marche:
            return False

        self.secondes_figees = self.secondes()
        self.en_marche = False
        self.en_pause = False

        return True


    def reinitialiser(self):

        self.depart = None
        self.temps_pause = None
        self.pause_totale = 0

        self.en_marche = False
        self.en_pause = False
        self.secondes_figees = 0


    def secondes(self):

        if self.depart is None:
            return 0

        if not self.en_marche:
            return self.secondes_figees

        if self.en_pause:
            return int(
                self.temps_pause
                - self.depart
                - self.pause_totale
            )

        return int(
            time.time()
            - self.depart
            - self.pause_totale
        )


    def temps(self):

        s = self.secondes()

        heures = s // 3600

        minutes = (s % 3600) // 60

        secondes = s % 60

        return heures, minutes, secondes


    def texte(self):

        h, m, s = self.temps()

        morceaux = []

        if h:
            morceaux.append(
                f"{h} heure{'s' if h > 1 else ''}"
            )

        if m:
            morceaux.append(
                f"{m} minute{'s' if m > 1 else ''}"
            )

        morceaux.append(
            f"{s} seconde{'s' if s > 1 else ''}"
        )

        return " ".join(morceaux)
    
    def afficher(self):
        while self.en_marche:
            print(self.texte(), end="\r")
            time.sleep(1)



chronometre = Chronometre()