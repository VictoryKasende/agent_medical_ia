from rest_framework import serializers

from .models import FicheConsultation


class FicheConsultationSerializer(serializers.ModelSerializer):
    """Serializer principal pour le modèle FicheConsultation.

    Remarques:
    - La majorité des champs sont exposés pour création / mise à jour.
    - Certains champs sont en lecture seule car gérés automatiquement côté serveur:
        * numero_dossier (généré dans save())
        * date_consultation, created_at, diagnostic_ia
        * medecin_validateur, date_validation, signature_medecin
    - Le champ `status` est en lecture seule ici; les transitions seront gérées via
      des actions dédiées (ex: validate, relancer-analyse) dans le ViewSet.
    - Ajout d'un champ dérivé `status_display` pour l'UI / clients.
    """

    status_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FicheConsultation
        fields = [
            # Identifiants & métadonnées
            'id', 'numero_dossier', 'date_consultation', 'created_at',
            # Patient identité
            'nom', 'postnom', 'prenom', 'date_naissance', 'age', 'sexe', 'telephone',
            'etat_civil', 'occupation',
            # Adresse
            'avenue', 'quartier', 'commune',
            # Personne à contacter
            'contact_nom', 'contact_telephone', 'contact_adresse',
            # Timings
            'heure_debut', 'heure_fin',
            # Signes vitaux
            'temperature', 'spo2', 'poids', 'tension_arterielle', 'pouls', 'frequence_respiratoire',
            # Présences
            'patient', 'proche', 'soignant', 'medecin', 'autre',
            'proche_lien', 'soignant_role', 'autre_precisions',
            # Anamnèse / symptômes
            'motif_consultation', 'histoire_maladie',
            'maison_medicaments', 'pharmacie_medicaments', 'centre_sante_medicaments', 'hopital_medicaments', 'medicaments_non_pris', 'details_medicaments',
            'cephalees', 'vertiges', 'palpitations', 'troubles_visuels', 'nycturie',
            # Antécédents
            'hypertendu', 'diabetique', 'epileptique', 'trouble_comportement', 'gastritique',
            'tabac', 'alcool', 'activite_physique', 'activite_physique_detail', 'alimentation_habituelle',
            'allergie_medicamenteuse', 'medicament_allergique',
            'familial_drepanocytaire', 'familial_diabetique', 'familial_obese', 'familial_hypertendu', 'familial_trouble_comportement',
            'lien_pere', 'lien_mere', 'lien_frere', 'lien_soeur',
            'evenement_traumatique', 'trauma_divorce', 'trauma_perte_parent', 'trauma_deces_epoux', 'trauma_deces_enfant',
            'etat_general', 'autres_antecedents',
            # Examen clinique
            'etat', 'par_quoi', 'capacite_physique', 'capacite_physique_score', 'capacite_psychologique', 'capacite_psychologique_score',
            'febrile', 'coloration_bulbaire', 'coloration_palpebrale', 'tegument',
            'tete', 'cou', 'paroi_thoracique', 'poumons', 'coeur', 'epigastre_hypochondres', 'peri_ombilical_flancs', 'hypogastre_fosses_iliaques', 'membres', 'colonne_bassin', 'examen_gynecologique',
            # Expériences patient
            'preoccupations', 'comprehension', 'attentes', 'engagement',
            # Consultation distante
            'is_patient_distance', 'status', 'status_display',
            # Résultats & validation
            'diagnostic', 'traitement', 'examen_complementaire', 'recommandations', 'diagnostic_ia',
            'medecin_validateur', 'date_validation', 'signature_medecin',
            'signature_medecin',
        ]
        read_only_fields = [
            'id', 'numero_dossier', 'date_consultation', 'created_at',
            'status', 'status_display', 'diagnostic_ia', 'medecin_validateur', 'date_validation', 'signature_medecin'
        ]

    def get_status_display(self, obj):
        return obj.get_status_display()

    def validate(self, attrs):
        # Place pour logique de validation transversale future (ex: cohérence âge/date_naissance)
        return super().validate(attrs)

from rest_framework import serializers
from .models import Conversation, MessageIA, FicheConsultation
from authentication.models import CustomUser
from .models import FicheConsultation, Conversation, MessageIA


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'role', 'is_staff'
        ]
        read_only_fields = ['id', 'is_staff']


class FicheConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FicheConsultation
        fields = '__all__'
        read_only_fields = [
            'numero_dossier', 'date_consultation', 'heure_debut', 'heure_fin', 'created_at',
            'medecin_validateur', 'date_validation'
        ]


class ConversationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'nom', 'user', 'fiche', 'created_at', 'updated_at', 'titre']
        read_only_fields = ['id', 'created_at', 'updated_at', 'titre', 'user']


class MessageIASerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageIA
        fields = ['id', 'conversation', 'role', 'content', 'timestamp']
        read_only_fields = ['id', 'timestamp', 'conversation']

class ConversationSerializer(serializers.ModelSerializer):
    messages_count = serializers.IntegerField(source='messageia_set.count', read_only=True)
    first_message = serializers.SerializerMethodField()
    fiche_numero = serializers.CharField(source='fiche.numero_dossier', read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'nom', 'titre', 'user', 'fiche', 'fiche_numero', 'created_at', 'updated_at', 'messages_count', 'first_message']
        read_only_fields = ['id', 'titre', 'user', 'created_at', 'updated_at', 'messages_count', 'first_message', 'fiche_numero']

    def get_first_message(self, obj):
        msg = obj.messageia_set.order_by('timestamp').first()
        return msg.content if msg else None

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        return super().create(validated_data)

class ConversationDetailSerializer(ConversationSerializer):
    messages = MessageIASerializer(source='messageia_set', many=True, read_only=True)

    class Meta(ConversationSerializer.Meta):
        fields = ConversationSerializer.Meta.fields + ['messages']
        read_only_fields = ConversationSerializer.Meta.read_only_fields + ['messages']
        read_only_fields = ['id', 'timestamp']
