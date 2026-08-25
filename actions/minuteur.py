import threading
import time

from actions.notifications import notifier_telephone


class Minuteur:

    def __init__(self):
        self.timer = None
        self.actif = False
        self.en_pause = False
        self.depart = None
        self.mode_pomodoro = False
        self.phase_pomodoro = None
        self.duree = 0
        self.restant_a_la_pause = 0

    def demarrer(self, minutes=0, secondes=0):

        if self.actif:
            return False

        self.duree = minutes * 60 + secondes

        if self.duree <= 0:
            return False

        self.depart = time.time()
        self.en_pause = False

        self.timer = threading.Timer(
            self.duree,
            self._sonner
        )

        self.timer.daemon = True
        self.timer.start()

        self.actif = True

        return True

    def demarrer_pomodoro(self):

        if self.actif:
            return False

        self.mode_pomodoro = True
        self.phase_pomodoro = "travail"

        return self.demarrer(25, 0)

    def pause(self):

        if not self.actif or self.en_pause:
            return False

        self.timer.cancel()

        self.restant_a_la_pause = self.temps_restant()
        self.en_pause = True

        return True

    def reprendre(self):

        if not self.actif or not self.en_pause:
            return False

        self.depart = time.time()
        self.duree = self.restant_a_la_pause

        self.timer = threading.Timer(
            self.duree,
            self._sonner
        )

        self.timer.daemon = True
        self.timer.start()

        self.en_pause = False

        return True

    def temps_restant(self):

        if not self.actif:
            return 0

        if self.en_pause:
            return int(self.restant_a_la_pause)

        ecoule = time.time() - self.depart

        return max(
            0,
            int(self.duree - ecoule)
        )

    def _sonner(self):

        self.actif = False

        # --------------------------------------------------
        # SON LOCAL DU DESKBOT
        # --------------------------------------------------
        try:
            from audio.voix import jouer_son

            jouer_son("sonneries/minuteur.mp3")

        except Exception as e:
            print("🔊 Son du minuteur indisponible :", e)

        # --------------------------------------------------
        # POMODORO : FIN DU TRAVAIL
        # --------------------------------------------------
        if (
            self.mode_pomodoro
            and self.phase_pomodoro == "travail"
        ):

            message = (
                "La session de travail est terminée. "
                "Les 5 minutes de pause commencent."
            )

            try:
                from audio.voix import parler

                parler(message)

            except Exception as e:
                print("🗣️ Voix indisponible :", e)

            notifier_telephone(
                "DeskBot",
                "Session terminée. Pause de 5 minutes."
            )

            self.phase_pomodoro = "pause"

            self.demarrer(5, 0)

        # --------------------------------------------------
        # POMODORO : FIN DE LA PAUSE
        # --------------------------------------------------
        elif (
            self.mode_pomodoro
            and self.phase_pomodoro == "pause"
        ):

            message = "Les 5 minutes de pause sont terminées."

            try:
                from audio.voix import parler

                parler(message)

            except Exception as e:
                print("🗣️ Voix indisponible :", e)

            notifier_telephone(
                "DeskBot",
                "Les 5 minutes de pause sont terminées."
            )

            self.mode_pomodoro = False
            self.phase_pomodoro = None

        # --------------------------------------------------
        # MINUTEUR NORMAL
        # --------------------------------------------------
        else:

            message = "Le minuteur est terminé."

            try:
                from audio.voix import parler

                parler(message)

            except Exception as e:
                print("🗣️ Voix indisponible :", e)

            notifier_telephone(
                "DeskBot",
                "Le minuteur est terminé."
            )

    def arreter(self):

        if not self.actif:
            return False

        self.timer.cancel()

        self.actif = False
        self.en_pause = False

        return True


minuteur = Minuteur()