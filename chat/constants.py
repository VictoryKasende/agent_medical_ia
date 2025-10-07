"""Domain constants for the chat app (consultations, statuses).

Centralisation des statuts de FicheConsultation pour éviter duplications
et simplifier la sérialisation / affichage.
"""

STATUS_EN_ANALYSE = "en_analyse"
STATUS_ANALYSE_TERMINEE = "analyse_terminee"
STATUS_VALIDE_MEDECIN = "valide_medecin"
STATUS_REJETE_MEDECIN = "rejete_medecin"

STATUS_CHOICES = [
    (STATUS_EN_ANALYSE, "En cours d'analyse"),
    (STATUS_ANALYSE_TERMINEE, "Analyse terminée"),
    (STATUS_VALIDE_MEDECIN, "Validé par médecin"),
    (STATUS_REJETE_MEDECIN, "Rejeté par médecin"),
]

STATUS_CHOICES_DICT = dict(STATUS_CHOICES)

__all__ = [
    "STATUS_EN_ANALYSE",
    "STATUS_ANALYSE_TERMINEE",
    "STATUS_VALIDE_MEDECIN",
    "STATUS_REJETE_MEDECIN",
    "STATUS_CHOICES",
    "STATUS_CHOICES_DICT",
]
