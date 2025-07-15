from django.db import models
from django.utils import timezone
from authentication.models import CustomUser


class FicheConsultation(models.Model):
    CELIBATAIRE = 'Célibataire'
    MARIE = 'Marié(e)'
    DIVORCE = 'Divorcé(e)'
    VEUF = 'Veuf(ve)'

    ETAT_CIVIL_CHOICES = [
        (CELIBATAIRE, 'Célibataire'),
        (MARIE, 'Marié(e)'),
        (DIVORCE, 'Divorcé(e)'),
        (VEUF, 'Veuf(ve)'),
    ]

    # Informations Patient
    nom = models.CharField(max_length=100)
    postnom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    age = models.IntegerField()
    sexe = models.CharField(max_length=10, choices=[('M', 'Masculin'), ('F', 'Féminin')], null=True)
    telephone = models.CharField(max_length=30)

    etat_civil = models.CharField(
        max_length=30,
        choices=ETAT_CIVIL_CHOICES,
        default=CELIBATAIRE,
    )
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
    pharmacie_medicaments = models.BooleanField(default=False, help_text="Des médicaments sont-ils pris à la pharmacie ?")
    centre_sante_medicaments = models.BooleanField(default=False, help_text="Des médicaments sont-ils pris au centre de santé ?")
    hopital_medicaments = models.BooleanField(default=False, help_text="Des médicaments sont-ils pris à l'hôpital ?")
    medicaments_non_pris = models.BooleanField(default=False, help_text="Des médicaments n'ont-ils pas été pris ?")
    details_medicaments = models.TextField(blank=True, null=True)

    cephalees = models.BooleanField(default=False, blank=True, null=True, help_text="Le patient a-t-il des céphalées ?")
    vertiges = models.BooleanField(default=False, blank=True, null=True, help_text="Le patient a-t-il des vertiges ?")
    palpitations = models.BooleanField(default=False, blank=True, null=True, help_text="Le patient a-t-il des palpitations ?")
    troubles_visuels = models.BooleanField(default=False, blank=True, null=True, help_text="Le patient a-t-il des troubles visuels ?")
    nycturie = models.BooleanField(default=False, blank=True, null=True, help_text="Le patient a-t-il des nycturies ?")

    # Antécédents
    hypertendu = models.BooleanField(default=False)
    diabetique = models.BooleanField(default=False)
    epileptique = models.BooleanField(default=False)
    trouble_comportement = models.BooleanField(default=False)
    gastritique = models.BooleanField(default=False)

    FREQUENCE = [
        ('non', 'Non'),
        ('rarement', 'Rarement'),
        ('souvent', 'Souvent'),
        ('tres_souvent', 'Très souvent'),
    ]
    tabac = models.CharField(max_length=20, choices=FREQUENCE, default='non')
    alcool = models.CharField(max_length=20, choices=FREQUENCE, default='non')
    activite_physique = models.CharField(max_length=20, choices=FREQUENCE, default='rarement')
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

    evenement_traumatique = models.CharField(
        max_length=10,
        choices=[('oui', 'Oui'), ('non', 'Non'), ('inconnu', 'Je ne sais pas')],
        default='non'
    )
    trauma_divorce = models.BooleanField(default=False)
    trauma_perte_parent = models.BooleanField(default=False)
    trauma_deces_epoux = models.BooleanField(default=False)
    trauma_deces_enfant = models.BooleanField(default=False)

    etat_general = models.TextField(max_length=255, blank=True, null=True)
    autres_antecedents = models.TextField(max_length=255, blank=True, null=True)

    # Examen clinique
    etat = models.CharField(max_length=20, choices=[('Conservé', 'Conservé'), ('Altéré', 'Altéré')])
    par_quoi = models.TextField(max_length=255, blank=True, null=True)
    capacite_physique = models.CharField(max_length=20, choices=[('Top', 'Top'), ('Moyen', 'Moyen'), ('Bas', 'Bas')])
    capacite_physique_score = models.CharField(max_length=10, blank=True, null=True)

    capacite_psychologique = models.CharField(max_length=20,
                                              choices=[('Top', 'Top'), ('Moyen', 'Moyen'), ('Bas', 'Bas')])
    capacite_psychologique_score = models.CharField(max_length=10, blank=True, null=True)

    febrile = models.CharField(max_length=10, choices=[('Oui', 'Oui'), ('Non', 'Non')])
    coloration_bulbaire = models.CharField(max_length=20, choices=[('Normale', 'Normale'), ('Anormale', 'Anormale')])
    coloration_palpebrale = models.CharField(max_length=20, choices=[('Normale', 'Normale'), ('Anormale', 'Anormale')])
    tegument = models.CharField(max_length=20, choices=[('Normal', 'Normal'), ('Anormal', 'Anormal')])

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

    # Nouveaux champs pour la consultation à distance
    is_patient_distance = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=[
        ('en_analyse', 'En cours d\'analyse'),
        ('analyse_terminee', 'Analyse terminée'),
        ('valide_medecin', 'Validé par médecin'),
        ('rejete_medecin', 'Rejeté par médecin'),
    ], default='en_analyse')

        # Ajoute ce dictionnaire juste ici
    STATUS_CHOICES_DICT = dict([
        ('en_analyse', 'En cours d\'analyse'),
        ('analyse_terminee', 'Analyse terminée'),
        ('valide_medecin', 'Validé par médecin'),
        ('rejete_medecin', 'Rejeté par médecin'),
    ])
    
    # Recommandations du medecin
    diagnostic = models.TextField(blank=True, null=True)
    traitement = models.TextField(blank=True, null=True)
    examen_complementaire = models.TextField(blank=True, null=True)
    recommandations = models.TextField(blank=True, null=True)
    medecin_validateur = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='consultations_validees'
    )
    date_validation = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    diagnostic_ia = models.TextField(blank=True, null=True)
    signature_medecin = models.ImageField(
        upload_to='signatures/', 
        blank=True, 
        null=True, 
        help_text="Signature du médecin pour valider la consultation"
    )
    
    def save(self, *args, **kwargs):
        if not self.heure_debut:
            self.heure_debut = timezone.localtime().time()

        if not self.numero_dossier:
            today = timezone.now().date()
            prefix = f"CONS-{today.strftime('%Y%m%d')}"
            count = FicheConsultation.objects.filter(date_consultation=today).count() + 1
            self.numero_dossier = f"{prefix}-{count:03d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Fiche Consultation - {self.nom} {self.postnom} ({self.numero_dossier})"

    class Meta:
        verbose_name = 'Fiche de Consultation'
        verbose_name_plural = 'Fiches de Consultation'
        ordering = ['-date_consultation']

class Conversation(models.Model):
    nom = models.CharField(max_length=100, blank=True, null=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="conversations")
    fiche = models.ForeignKey(FicheConsultation, on_delete=models.CASCADE, related_name="conversations", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def titre(self):
        if self.nom:
            return self.nom
        msg = self.messageia_set.filter(role='user').first()
        return msg.content[:30] + '...' if msg else 'Conversation'

    def __str__(self):
        if self.fiche:
            return f"Conversation #{self.id} - {self.user.username} (Fiche {self.fiche.numero_dossier})"
        return f"Conversation #{self.id} - {self.user.username}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'

class MessageIA(models.Model):
    ROLE_CHOICES = [
        ('user', 'Utilisateur'),
        ('gpt4', 'GPT-4'),
        ('claude', 'Claude 3'),
        ('gemini', 'Gemini Pro'),
        ('synthese', 'Synthèse Finale'),
    ]

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.get_role_display()}] {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'Message IA'
        verbose_name_plural = 'Messages IA'



