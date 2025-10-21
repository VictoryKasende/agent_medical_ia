from django.db import models
from django.utils import timezone

from authentication.models import CustomUser

from .constants import (
    STATUS_ANALYSE_TERMINEE,
    STATUS_CHOICES,
    STATUS_CHOICES_DICT,
    STATUS_EN_ANALYSE,
    STATUS_REJETE_MEDECIN,
    STATUS_VALIDE_MEDECIN,
)


class FicheConsultation(models.Model):
    class EtatCivil(models.TextChoices):
        CELIBATAIRE = "Célibataire", "Célibataire"
        MARIE = "Marié(e)", "Marié(e)"
        DIVORCE = "Divorcé(e)", "Divorcé(e)"
        VEUF = "Veuf(ve)", "Veuf(ve)"

    # Informations Patient
    nom = models.CharField(max_length=100)
    postnom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    age = models.IntegerField()
    sexe = models.CharField(max_length=10, choices=[("M", "Masculin"), ("F", "Féminin")], null=True)
    telephone = models.CharField(max_length=30)

    etat_civil = models.CharField(max_length=30, choices=EtatCivil.choices, default=EtatCivil.CELIBATAIRE)
    occupation = models.CharField(max_length=100)

    # Adresse
    avenue = models.CharField(max_length=100)
    quartier = models.CharField(max_length=100)
    commune = models.CharField(max_length=100)

    # Personne à contacter
    contact_nom = models.CharField(max_length=100)
    contact_telephone = models.CharField(max_length=30)
    contact_adresse = models.CharField(max_length=255)

    date_consultation = models.DateField(auto_now_add=True)
    heure_debut = models.TimeField(blank=True, null=True)
    heure_fin = models.TimeField(blank=True, null=True)
    numero_dossier = models.CharField(max_length=50, unique=True, blank=True)
    # Lien patient (créateur propriétaire)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="fiches", null=True, blank=True)

    # Signes vitaux
    temperature = models.FloatField(help_text="Température en °C", null=True, blank=True)
    spo2 = models.IntegerField(help_text="Saturation en oxygène (%)", null=True, blank=True)
    poids = models.FloatField(help_text="Poids en kg", null=True, blank=True)
    tension_arterielle = models.CharField(max_length=20, help_text="Ex: 120/80", null=True, blank=True)
    pouls = models.IntegerField(help_text="Pouls (battements/minute)", null=True, blank=True)
    frequence_respiratoire = models.IntegerField(help_text="FR (mouvements/minute)", null=True, blank=True)

    patient = models.BooleanField(default=True, help_text="Le patient est-il présent ?")
    proche = models.BooleanField(default=False, help_text="Un proche est-il présent ?")
    soignant = models.BooleanField(default=False, help_text="Un soignant est-il présent ?")
    medecin = models.BooleanField(default=False, help_text="Un médecin est-il présent ?")
    autre = models.BooleanField(default=False, help_text="Un autre intervenant est-il présent ?")

    proche_lien = models.CharField(max_length=100, blank=True, null=True)
    soignant_role = models.CharField(max_length=100, blank=True, null=True)
    autre_precisions = models.CharField(max_length=100, blank=True, null=True)

    # Anamnèse
    motif_consultation = models.TextField(blank=True, null=True)
    histoire_maladie = models.TextField(blank=True, null=True)

    maison_medicaments = models.BooleanField(default=False, help_text="Des médicaments sont-ils pris à la maison ?")
    pharmacie_medicaments = models.BooleanField(
        default=False, help_text="Des médicaments sont-ils pris à la pharmacie ?"
    )
    centre_sante_medicaments = models.BooleanField(
        default=False, help_text="Des médicaments sont-ils pris au centre de santé ?"
    )
    hopital_medicaments = models.BooleanField(default=False, help_text="Des médicaments sont-ils pris à l'hôpital ?")
    medicaments_non_pris = models.BooleanField(default=False, help_text="Des médicaments n'ont-ils pas été pris ?")
    details_medicaments = models.TextField(blank=True, null=True)

    cephalees = models.BooleanField(default=False, blank=True, null=True, help_text="Le patient a-t-il des céphalées ?")
    vertiges = models.BooleanField(default=False, blank=True, null=True, help_text="Le patient a-t-il des vertiges ?")
    palpitations = models.BooleanField(
        default=False, blank=True, null=True, help_text="Le patient a-t-il des palpitations ?"
    )
    troubles_visuels = models.BooleanField(
        default=False, blank=True, null=True, help_text="Le patient a-t-il des troubles visuels ?"
    )
    nycturie = models.BooleanField(default=False, blank=True, null=True, help_text="Le patient a-t-il des nycturies ?")

    # Antécédents
    hypertendu = models.BooleanField(default=False)
    diabetique = models.BooleanField(default=False)
    epileptique = models.BooleanField(default=False)
    trouble_comportement = models.BooleanField(default=False)
    gastritique = models.BooleanField(default=False)

    class Frequence(models.TextChoices):
        NON = "non", "Non"
        RAREMENT = "rarement", "Rarement"
        SOUVENT = "souvent", "Souvent"
        TRES_SOUVENT = "tres_souvent", "Très souvent"

    tabac = models.CharField(max_length=20, choices=Frequence.choices, default=Frequence.NON)
    alcool = models.CharField(max_length=20, choices=Frequence.choices, default=Frequence.NON)
    activite_physique = models.CharField(max_length=20, choices=Frequence.choices, default=Frequence.RAREMENT)
    activite_physique_detail = models.TextField(blank=True, null=True)
    alimentation_habituelle = models.TextField(blank=True, null=True)

    allergie_medicamenteuse = models.BooleanField(default=False)
    medicament_allergique = models.CharField(max_length=255, blank=True, null=True)

    familial_drepanocytaire = models.BooleanField(default=False)
    familial_diabetique = models.BooleanField(default=False)
    familial_obese = models.BooleanField(default=False)
    familial_hypertendu = models.BooleanField(default=False)
    familial_trouble_comportement = models.BooleanField(default=False)

    lien_pere = models.BooleanField(default=False)
    lien_mere = models.BooleanField(default=False)
    lien_frere = models.BooleanField(default=False)
    lien_soeur = models.BooleanField(default=False)

    class OuiNonInconnu(models.TextChoices):
        OUI = "oui", "Oui"
        NON = "non", "Non"
        INCONNU = "inconnu", "Je ne sais pas"

    evenement_traumatique = models.CharField(max_length=10, choices=OuiNonInconnu.choices, default=OuiNonInconnu.NON)
    trauma_divorce = models.BooleanField(default=False)
    trauma_perte_parent = models.BooleanField(default=False)
    trauma_deces_epoux = models.BooleanField(default=False)
    trauma_deces_enfant = models.BooleanField(default=False)

    etat_general = models.TextField(max_length=255, blank=True, null=True)
    autres_antecedents = models.TextField(max_length=255, blank=True, null=True)

    # Examen clinique
    class Etat(models.TextChoices):
        CONSERVE = "Conservé", "Conservé"
        ALTERE = "Altéré", "Altéré"

    etat = models.CharField(max_length=20, choices=Etat.choices)
    par_quoi = models.TextField(max_length=255, blank=True, null=True)

    class Capacite(models.TextChoices):
        TOP = "Top", "Top"
        MOYEN = "Moyen", "Moyen"
        BAS = "Bas", "Bas"

    capacite_physique = models.CharField(max_length=20, choices=Capacite.choices)
    capacite_physique_score = models.CharField(max_length=10, blank=True, null=True)

    capacite_psychologique = models.CharField(max_length=20, choices=Capacite.choices)
    capacite_psychologique_score = models.CharField(max_length=10, blank=True, null=True)

    class OuiNon(models.TextChoices):
        OUI = "Oui", "Oui"
        NON = "Non", "Non"

    class ColorationBulbaire(models.TextChoices):
        NORMALE = "normale", "Normale"
        JAUNATRE = "jaunatre", "Jaunâtre"
        ROUGEATRE = "rougeatre", "Rougeâtre"

    class ColorationPalpebrale(models.TextChoices):
        NORMALE = "normale", "Normale"
        PALE = "pale", "Pâle"

    febrile = models.CharField(max_length=10, choices=OuiNon.choices)
    coloration_bulbaire = models.CharField(
        max_length=20, choices=ColorationBulbaire.choices, default=ColorationBulbaire.NORMALE
    )
    coloration_palpebrale = models.CharField(
        max_length=20, choices=ColorationPalpebrale.choices, default=ColorationPalpebrale.NORMALE
    )

    class Tegument(models.TextChoices):
        NORMAL = "Normal", "Normal"
        ANORMAL = "Anormal", "Anormal"

    tegument = models.CharField(max_length=20, choices=Tegument.choices)

    # Régions examinées
    tete = models.TextField(blank=True, null=True)
    cou = models.TextField(blank=True, null=True)
    paroi_thoracique = models.TextField(blank=True, null=True)
    poumons = models.TextField(blank=True, null=True)
    coeur = models.TextField(blank=True, null=True)
    epigastre_hypochondres = models.TextField(blank=True, null=True)
    peri_ombilical_flancs = models.TextField(blank=True, null=True)
    hypogastre_fosses_iliaques = models.TextField(blank=True, null=True)
    membres = models.TextField(blank=True, null=True)
    colonne_bassin = models.TextField(blank=True, null=True)
    examen_gynecologique = models.TextField(blank=True, null=True)

    # Expériences et perceptions du patient
    preoccupations = models.TextField(blank=True, null=True)
    comprehension = models.TextField(blank=True, null=True)
    attentes = models.TextField(blank=True, null=True)
    engagement = models.TextField(blank=True, null=True)

    # Nouveaux champs pour améliorer l'analyse IA
    hypothese_patient_medecin = models.TextField(
        blank=True, null=True, help_text="À quoi pensez-vous ? Hypothèse diagnostique du patient ou médecin"
    )
    analyses_proposees = models.TextField(blank=True, null=True, help_text="Analyses paracliniques que vous proposez")

    # Nouveaux champs pour la consultation à distance
    is_patient_distance = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_EN_ANALYSE)
    commentaire_rejet = models.TextField(blank=True, null=True, help_text="Motif détaillé en cas de rejet")

    # Recommandations du medecin
    diagnostic = models.TextField(blank=True, null=True)
    traitement = models.TextField(blank=True, null=True)
    examen_complementaire = models.TextField(blank=True, null=True)
    recommandations = models.TextField(blank=True, null=True)
    medecin_validateur = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="consultations_validees"
    )
    assigned_medecin = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consultations_assignees",
        help_text="Médecin assigné pour le suivi de la consultation",
    )
    date_validation = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    diagnostic_ia = models.TextField(blank=True, null=True)
    signature_medecin = models.FileField(
        upload_to="signatures/", blank=True, null=True, help_text="Signature du médecin pour valider la consultation"
    )

    def save(self, *args, **kwargs):
        if not self.heure_debut:
            self.heure_debut = timezone.localtime().time()

        if not self.numero_dossier:
            from django.conf import settings

            # Mode test : numérotation simplifiée pour éviter les collisions
            if getattr(settings, "TESTING", False) or "test" in str(settings.DATABASES["default"]["NAME"]):

                import random
                import time

                timestamp = int(time.time() * 1000) % 1000000
                random_suffix = random.randint(100, 999)
                self.numero_dossier = f"TEST-{timestamp:06d}-{random_suffix}"
            else:
                # Mode production : numérotation standard
                today = timezone.now().date()
                prefix = f"CONS-{today.strftime('%Y%m%d')}"

                # Approche robuste pour éviter les doublons
                from django.db import transaction

                with transaction.atomic():
                    # Obtenir le dernier numéro pour aujourd'hui
                    last_fiche = (
                        FicheConsultation.objects.filter(date_consultation=today, numero_dossier__startswith=prefix)
                        .order_by("-numero_dossier")
                        .first()
                    )

                    if last_fiche and last_fiche.numero_dossier:
                        # Extraire le numéro et incrémenter
                        try:
                            last_num = int(last_fiche.numero_dossier.split("-")[-1])
                            count = last_num + 1
                        except (ValueError, IndexError):
                            count = FicheConsultation.objects.filter(date_consultation=today).count() + 1
                    else:
                        count = 1

                    # Générer un numéro unique avec retry en cas de collision
                    max_attempts = 10
                    for attempt in range(max_attempts):
                        numero = f"{prefix}-{count:03d}"
                        if not FicheConsultation.objects.filter(numero_dossier=numero).exists():
                            self.numero_dossier = numero
                            break
                        count += 1
                    else:
                        # Fallback avec timestamp si impossible de générer un numéro unique
                        import time

                        timestamp = int(time.time() * 1000) % 10000  # 4 derniers chiffres
                        self.numero_dossier = f"{prefix}-{timestamp:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Fiche Consultation - {self.nom} {self.postnom} ({self.numero_dossier})"

    class Meta:
        verbose_name = "Fiche de Consultation"
        verbose_name_plural = "Fiches de Consultation"
        ordering = ["-date_consultation"]


class Conversation(models.Model):
    nom = models.CharField(max_length=100, blank=True, null=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="conversations")
    fiche = models.ForeignKey(
        FicheConsultation, on_delete=models.CASCADE, related_name="conversations", null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def titre(self):
        if self.nom:
            return self.nom
        msg = self.messageia_set.filter(role="user").first()
        return msg.content[:30] + "..." if msg else "Conversation"

    def __str__(self):
        if self.fiche:
            return f"Conversation #{self.id} - {self.user.username} (Fiche {self.fiche.numero_dossier})"
        return f"Conversation #{self.id} - {self.user.username}"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"


class MessageIA(models.Model):
    class Role(models.TextChoices):
        USER = "user", "Utilisateur"
        GPT4 = "gpt4", "GPT-4"
        CLAUDE = "claude", "Claude 3"
        GEMINI = "gemini", "Gemini Pro"
        SYNTHESE = "synthese", "Synthèse Finale"

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=Role.choices)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.get_role_display()}] {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

    class Meta:
        ordering = ["timestamp"]
        verbose_name = "Message IA"
        verbose_name_plural = "Messages IA"


class Appointment(models.Model):
    """Rendez-vous patient <-> médecin.

    Flux attendu:
    - Un patient crée une demande de rendez-vous (requested_start/end ou slot unique).
    - Un médecin assigne/valide un créneau et confirme; ou décline avec un motif.
    - Statuts sous forme d'enum stables pour le schéma OpenAPI.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        CONFIRMED = "confirmed", "Confirmé"
        DECLINED = "declined", "Refusé"
        CANCELLED = "cancelled", "Annulé"

    class ConsultationMode(models.TextChoices):
        PRESENTIEL = "presentiel", "Présentiel"
        DISTANCIEL = "distanciel", "Distanciel/Téléconsultation"

    patient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="appointments_as_patient")
    medecin = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="appointments_as_medecin"
    )
    fiche = models.ForeignKey(
        "FicheConsultation", on_delete=models.SET_NULL, null=True, blank=True, related_name="appointments"
    )

    # Créneau demandé par le patient
    requested_start = models.DateTimeField()
    requested_end = models.DateTimeField()

    # Créneau confirmé par le médecin (peut être identique ou ajusté)
    confirmed_start = models.DateTimeField(null=True, blank=True)
    confirmed_end = models.DateTimeField(null=True, blank=True)

    # Nouveau: mode et localisation
    consultation_mode = models.CharField(
        max_length=20,
        choices=ConsultationMode.choices,
        default=ConsultationMode.DISTANCIEL,
        help_text="Mode de consultation",
    )
    location_note = models.TextField(
        blank=True, null=True, help_text="Adresse ou informations de connexion selon le mode"
    )

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    message_patient = models.TextField(blank=True, null=True)
    message_medecin = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        who = f"{self.patient.username}"
        if self.medecin:
            who += f" ↔ Dr {self.medecin.username}"
        return f"RDV {self.id} [{self.get_status_display()}] {who} ({self.get_consultation_mode_display()})"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Rendez-vous"
        verbose_name_plural = "Rendez-vous"


class FicheMessage(models.Model):
    """Messages courts entre patient et médecin autour d'une fiche donnée."""

    fiche = models.ForeignKey(FicheConsultation, on_delete=models.CASCADE, related_name="messages")
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="fiche_messages")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Message Fiche"
        verbose_name_plural = "Messages Fiche"


class FicheReference(models.Model):
    """Références bibliographiques associées à une fiche de consultation."""

    fiche = models.ForeignKey(FicheConsultation, on_delete=models.CASCADE, related_name="references")
    title = models.CharField(max_length=255, help_text="Titre de la référence")
    url = models.URLField(blank=True, null=True, help_text="URL de la référence")
    source = models.CharField(
        max_length=50,
        choices=[
            ("pubmed", "PubMed"),
            ("cinahl", "CINAHL"),
            ("has", "HAS (Haute Autorité de Santé)"),
            ("cochrane", "Cochrane"),
            ("other", "Autre"),
        ],
        default="other",
        help_text="Source de la référence",
    )
    authors = models.CharField(max_length=500, blank=True, null=True, help_text="Auteurs")
    year = models.IntegerField(blank=True, null=True, help_text="Année de publication")
    journal = models.CharField(max_length=255, blank=True, null=True, help_text="Journal/Revue")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.get_source_display()})"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Référence Fiche"
        verbose_name_plural = "Références Fiche"


class LabResult(models.Model):
    """Résultats de laboratoire associés à une fiche de consultation."""

    fiche = models.ForeignKey(FicheConsultation, on_delete=models.CASCADE, related_name="lab_results")
    type_analyse = models.CharField(
        max_length=100, help_text="Type d'analyse (ex: Glycémie, Hémoglobine, Créatinine, etc.)"
    )
    valeur = models.CharField(max_length=50, help_text="Valeur du résultat")
    unite = models.CharField(max_length=20, blank=True, null=True, help_text="Unité de mesure")
    valeurs_normales = models.CharField(max_length=100, blank=True, null=True, help_text="Plage de valeurs normales")
    date_prelevement = models.DateField(help_text="Date du prélèvement")
    laboratoire = models.CharField(max_length=255, blank=True, null=True, help_text="Nom du laboratoire")
    fichier = models.FileField(
        upload_to="lab_results/", blank=True, null=True, help_text="Fichier PDF/image du résultat"
    )
    commentaire = models.TextField(blank=True, null=True, help_text="Commentaire du laboratoire")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type_analyse}: {self.valeur} {self.unite or ''} (Fiche {self.fiche.numero_dossier})"

    class Meta:
        ordering = ["-date_prelevement", "-created_at"]
        verbose_name = "Résultat de Laboratoire"
        verbose_name_plural = "Résultats de Laboratoire"


class FicheAttachment(models.Model):
    """Fichiers et pièces jointes associés à une fiche de consultation."""

    class AttachmentKind(models.TextChoices):
        IMAGE = "image", "Image/Photo"
        DOCUMENT = "document", "Document"
        XRAY = "xray", "Radiographie"
        SCAN = "scan", "Scanner/IRM"
        PRESCRIPTION = "prescription", "Ordonnance"
        OTHER = "other", "Autre"

    fiche = models.ForeignKey(FicheConsultation, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="attachments/%Y/%m/", help_text="Fichier joint")
    kind = models.CharField(
        max_length=20, choices=AttachmentKind.choices, default=AttachmentKind.OTHER, help_text="Type de pièce jointe"
    )
    note = models.TextField(blank=True, null=True, help_text="Description/note sur le fichier")
    uploaded_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name="uploaded_attachments"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_kind_display()} - {self.file.name} (Fiche {self.fiche.numero_dossier})"

    @property
    def file_size(self):
        """Taille du fichier en bytes."""
        try:
            return self.file.size
        except:
            return 0

    @property
    def file_extension(self):
        """Extension du fichier."""
        import os

        return os.path.splitext(self.file.name)[1].lower()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Pièce Jointe"
        verbose_name_plural = "Pièces Jointes"


class MedecinAvailability(models.Model):
    """Créneaux de disponibilité des médecins pour les consultations."""

    class DayOfWeek(models.IntegerChoices):
        LUNDI = 0, "Lundi"
        MARDI = 1, "Mardi"
        MERCREDI = 2, "Mercredi"
        JEUDI = 3, "Jeudi"
        VENDREDI = 4, "Vendredi"
        SAMEDI = 5, "Samedi"
        DIMANCHE = 6, "Dimanche"

    class ConsultationType(models.TextChoices):
        PRESENTIEL = "presentiel", "Présentiel"
        DISTANCIEL = "distanciel", "Distanciel"
        BOTH = "both", "Les deux"

    medecin = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="availabilities", limit_choices_to={"role": "medecin"}
    )
    day_of_week = models.IntegerField(choices=DayOfWeek.choices, help_text="Jour de la semaine (0=Lundi, 6=Dimanche)")
    start_time = models.TimeField(help_text="Heure de début du créneau")
    end_time = models.TimeField(help_text="Heure de fin du créneau")
    consultation_type = models.CharField(
        max_length=20,
        choices=ConsultationType.choices,
        default=ConsultationType.BOTH,
        help_text="Type de consultation accepté",
    )
    duration_minutes = models.IntegerField(default=30, help_text="Durée d'une consultation en minutes")
    is_active = models.BooleanField(default=True, help_text="Créneau actif")
    max_consultations = models.IntegerField(default=1, help_text="Nombre maximum de consultations sur ce créneau")
    location = models.CharField(
        max_length=255, blank=True, null=True, help_text="Lieu pour consultations présentielles"
    )
    notes = models.TextField(blank=True, null=True, help_text="Notes privées du médecin sur ce créneau")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dr {self.medecin.username} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"

    @property
    def duration_formatted(self):
        """Durée formatée en heures/minutes."""
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        if hours > 0:
            return f"{hours}h{minutes:02d}" if minutes > 0 else f"{hours}h"
        return f"{minutes}min"

    def is_available_on_date(self, date, consultation_type=None):
        """Vérifie si le médecin est disponible à cette date et heure."""
        if not self.is_active:
            return False

        if date.weekday() != self.day_of_week:
            return False

        if consultation_type and self.consultation_type not in [consultation_type, "both"]:
            return False

        # Vérifier les créneaux déjà pris
        existing_appointments = Appointment.objects.filter(
            medecin=self.medecin, confirmed_start__date=date.date(), status__in=["confirmed", "pending"]
        ).count()

        return existing_appointments < self.max_consultations

    class Meta:
        ordering = ["day_of_week", "start_time"]
        verbose_name = "Disponibilité Médecin"
        verbose_name_plural = "Disponibilités Médecin"
        unique_together = ["medecin", "day_of_week", "start_time", "end_time"]


class MedecinException(models.Model):
    """Exceptions aux disponibilités (congés, formations, etc.)."""

    class ExceptionType(models.TextChoices):
        UNAVAILABLE = "unavailable", "Indisponible"
        BUSY = "busy", "Occupé"
        VACATION = "vacation", "Congé"
        FORMATION = "formation", "Formation"
        EMERGENCY = "emergency", "Urgence"

    medecin = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="exceptions", limit_choices_to={"role": "medecin"}
    )
    start_datetime = models.DateTimeField(help_text="Début de l'exception")
    end_datetime = models.DateTimeField(help_text="Fin de l'exception")
    exception_type = models.CharField(max_length=20, choices=ExceptionType.choices, default=ExceptionType.UNAVAILABLE)
    reason = models.TextField(blank=True, null=True, help_text="Raison de l'indisponibilité")
    is_recurring = models.BooleanField(default=False, help_text="Exception récurrente (chaque semaine)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dr {self.medecin.username} - {self.get_exception_type_display()} du {self.start_datetime} au {self.end_datetime}"

    def is_active_on(self, datetime_obj):
        """Vérifie si l'exception est active à cette date/heure."""
        return self.start_datetime <= datetime_obj <= self.end_datetime

    class Meta:
        ordering = ["-start_datetime"]
        verbose_name = "Exception Médecin"
        verbose_name_plural = "Exceptions Médecin"


class WebhookEvent(models.Model):
    """Log des webhooks entrants (WhatsApp, SMS, etc.)."""

    class EventType(models.TextChoices):
        WHATSAPP_INCOMING = "whatsapp_incoming", "WhatsApp Entrant"
        SMS_INCOMING = "sms_incoming", "SMS Entrant"
        WHATSAPP_STATUS = "whatsapp_status", "Statut WhatsApp"
        SMS_STATUS = "sms_status", "Statut SMS"

    class ProcessingStatus(models.TextChoices):
        PENDING = "pending", "En attente"
        PROCESSED = "processed", "Traité"
        FAILED = "failed", "Échec"
        IGNORED = "ignored", "Ignoré"

    event_type = models.CharField(max_length=30, choices=EventType.choices)
    external_id = models.CharField(max_length=255, help_text="ID externe du message (Twilio SID, etc.)")
    sender_phone = models.CharField(max_length=30, help_text="Numéro de téléphone expéditeur")
    recipient_phone = models.CharField(max_length=30, help_text="Numéro de téléphone destinataire")
    content = models.TextField(help_text="Contenu du message")
    raw_payload = models.JSONField(help_text="Payload brut du webhook")
    processing_status = models.CharField(
        max_length=20, choices=ProcessingStatus.choices, default=ProcessingStatus.PENDING
    )
    processing_error = models.TextField(blank=True, null=True, help_text="Erreur de traitement")
    related_user = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, help_text="Utilisateur associé (si trouvé)"
    )
    related_fiche = models.ForeignKey(
        FicheConsultation, on_delete=models.SET_NULL, null=True, blank=True, help_text="Fiche associée (si trouvée)"
    )
    created_message = models.ForeignKey(
        "FicheMessage", on_delete=models.SET_NULL, null=True, blank=True, help_text="Message créé suite au webhook"
    )
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.sender_phone} ({self.get_processing_status_display()})"

    def mark_processed(self, message=None):
        """Marque le webhook comme traité."""
        self.processing_status = self.ProcessingStatus.PROCESSED
        self.processed_at = timezone.now()
        if message:
            self.created_message = message
        self.save()

    def mark_failed(self, error):
        """Marque le webhook comme échoué."""
        self.processing_status = self.ProcessingStatus.FAILED
        self.processing_error = str(error)
        self.processed_at = timezone.now()
        self.save()

    class Meta:
        ordering = ["-received_at"]
        verbose_name = "Événement Webhook"
        verbose_name_plural = "Événements Webhook"
        indexes = [
            models.Index(fields=["sender_phone"]),
            models.Index(fields=["external_id"]),
            models.Index(fields=["processing_status"]),
        ]


class DataExportJob(models.Model):
    """Jobs d'export de données pour biostatistiques."""

    class ExportFormat(models.TextChoices):
        CSV = "csv", "CSV"
        PARQUET = "parquet", "Parquet"
        JSON = "json", "JSON"
        EXCEL = "excel", "Excel"

    class ExportStatus(models.TextChoices):
        PENDING = "pending", "En attente"
        RUNNING = "running", "En cours"
        COMPLETED = "completed", "Terminé"
        FAILED = "failed", "Échec"

    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="export_jobs")
    export_format = models.CharField(max_length=20, choices=ExportFormat.choices, default=ExportFormat.CSV)
    date_start = models.DateField(help_text="Date de début pour l'export")
    date_end = models.DateField(help_text="Date de fin pour l'export")
    include_personal_data = models.BooleanField(
        default=False, help_text="Inclure les données personnelles (nom, téléphone, etc.)"
    )
    filters = models.JSONField(default=dict, help_text="Filtres appliqués (status, age_range, etc.)")
    status = models.CharField(max_length=20, choices=ExportStatus.choices, default=ExportStatus.PENDING)
    file_path = models.CharField(max_length=500, blank=True, null=True, help_text="Chemin du fichier généré")
    file_size = models.BigIntegerField(null=True, blank=True, help_text="Taille du fichier en bytes")
    records_count = models.IntegerField(null=True, blank=True, help_text="Nombre d'enregistrements exportés")
    error_message = models.TextField(blank=True, null=True, help_text="Message d'erreur si échec")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"Export {self.export_format.upper()} - {self.date_start} à {self.date_end} ({self.get_status_display()})"
        )

    @property
    def duration(self):
        """Durée de l'export."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

    @property
    def file_size_formatted(self):
        """Taille formatée du fichier."""
        if not self.file_size:
            return "N/A"

        for unit in ["B", "KB", "MB", "GB"]:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Job Export Données"
        verbose_name_plural = "Jobs Export Données"
