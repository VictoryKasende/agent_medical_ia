from rest_framework import serializers
from .models import FicheConsultation

class FicheConsultationDistanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FicheConsultation
        fields = '__all__'
        read_only_fields = [
            'numero_dossier', 'date_consultation', 'heure_debut', 'heure_fin', 'created_at',
            'diagnostic_ia', 'date_validation', 'medecin_validateur'
        ]
