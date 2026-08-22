from pydantic import BaseModel, ConfigDict
from typing import List
from actions.ia import generer_avec_groq
from actions.cours import obtenir_texte_chapitre
from actions.profil_revision import ajouter_points, ajouter_resultat_matiere, enregistrer_revision_terminee


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str
    reponse_attendue: str


class ListeQuestions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    questions: list[Question]


class Evaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    correcte: bool
    explication: str


def generer_questions(matiere, chapitre, nombre=5):
    """Genere une liste de (question, reponse_attendue) a partir d'un chapitre stocke."""

    texte_cours = obtenir_texte_chapitre(matiere, chapitre)

    if texte_cours is None:
        return None

    prompt = (
        f"Voici un cours scolaire. Génère {nombre} questions de révision pertinentes "
        "qui testent la compréhension des notions importantes (définitions, exemples, "
        "méthodes de calcul, chiffres clés). Varie les types de questions. Pour chaque "
        "question, donne la réponse attendue de façon concise et claire.\n\n"
        f"Cours :\n{texte_cours}"
    )

    resultat = generer_avec_groq(prompt, ListeQuestions)

    if resultat is None:
        return None

    return [(q.question, q.reponse_attendue) for q in resultat.questions]


def evaluer_reponse(question, reponse_attendue, reponse_utilisateur):
    """Retourne (correcte: bool, explication: str), tolerant sur la formulation."""

    prompt = (
        f"Question de révision : {question}\n"
        f"Réponse attendue : {reponse_attendue}\n"
        f"Réponse de l'élève : {reponse_utilisateur}\n\n"
        "L'élève a-t-il correctement répondu, même avec une formulation différente ? "
        "Sois tolérant sur la formulation mais strict sur le sens et les informations "
        "factuelles (chiffres, noms, définitions). Donne une explication brève."
    )

    resultat = generer_avec_groq(prompt, Evaluation)

    if resultat is None:
        return False, "Aucun service IA disponible pour évaluer ta réponse."

    return resultat.correcte, resultat.explication


class SessionRevision:

    def __init__(self):
        self.active = False
        self.questions_restantes = []
        self.questions_a_revoir = []
        self.question_actuelle = None
        self.nb_total = 0
        self.nb_correctes = 0
        self.nb_incorrectes = 0
        self.nb_tentatives = 0
        self.deja_ratees = set()
        self.phase_revoir = False
        self.matiere = ""

    def demarrer(self, questions, matiere=""):
        self.__init__()
        self.active = True
        self.questions_restantes = list(questions)
        self.nb_total = len(questions)
        self.matiere = matiere

    def question_suivante(self):
        if self.questions_restantes:
            self.question_actuelle = self.questions_restantes.pop(0)
            return self.question_actuelle[0]

        if not self.phase_revoir and self.questions_a_revoir:
            self.phase_revoir = True
            self.questions_restantes = self.questions_a_revoir
            self.questions_a_revoir = []
            self.question_actuelle = self.questions_restantes.pop(0)
            return self.question_actuelle[0]

        # La révision est complètement terminée
        self.active = False

        enregistrer_revision_terminee()

        return None

    def repondre(self, reponse_utilisateur):
        question, reponse_attendue = self.question_actuelle
        correcte, explication = evaluer_reponse(question, reponse_attendue, reponse_utilisateur)

        self.nb_tentatives += 1

        if correcte:
            self.nb_correctes += 1
            if correcte and self.question_actuelle not in self.deja_ratees:
                ajouter_points(1)
        else:
            self.nb_incorrectes += 1
            self.deja_ratees.add(self.question_actuelle)
            self.questions_a_revoir.append(self.question_actuelle)

        ajouter_resultat_matiere(self.matiere, correcte)

        return correcte, explication

    def stats(self):
        pourcentage = round(100 * (self.nb_total - len(self.deja_ratees)) / self.nb_total) if self.nb_total else 0
        return {
            "nb_total": self.nb_total,
            "nb_tentatives": self.nb_tentatives,
            "nb_correctes": self.nb_correctes,
            "nb_incorrectes": self.nb_incorrectes,
            "pourcentage_premier_coup": pourcentage,
            "note_sur_5": round(pourcentage / 20)
        }

    def arreter(self):
        self.active = False


session_revision = SessionRevision()