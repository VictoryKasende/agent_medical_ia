#!/usr/bin/env python
"""
Test API rapide pour CI/CD - Version simplifiée
"""

import os
import sys
import django
import requests
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agent_medical_ia.settings_test')
django.setup()

def test_basic_api():
    """Tests API de base rapides"""
    print("🧪 Tests API rapides pour CI/CD")
    
    # Test que Django démarre
    try:
        from django.conf import settings
        print("✅ Django settings chargés")
    except Exception as e:
        print(f"❌ Django: {e}")
        return False
    
    # Test que les modèles s'importent
    try:
        from chat.models import FicheConsultation, LabResult
        print("✅ Modèles P0/P1 importés")
    except Exception as e:
        print(f"❌ Modèles: {e}")
        return False
    
    # Test que les API views s'importent
    try:
        from chat.api_views import FicheConsultationViewSet
        print("✅ API ViewSets importés")
    except Exception as e:
        print(f"❌ API Views: {e}")
        return False
    
    # Test que les URLs se résolvent
    try:
        from django.urls import reverse
        url = reverse('chat_api:fiche-consultation-list')
        print(f"✅ URLs résolues: {url}")
    except Exception as e:
        print(f"❌ URLs: {e}")
        return False
    
    return True

def test_basic_model_creation():
    """Test création basique de modèles"""
    try:
        from django.contrib.auth import get_user_model
        from chat.models import FicheConsultation
        
        User = get_user_model()
        
        # Créer utilisateur test
        user = User.objects.create_user(
            username='test_api',
            email='test@api.com',
            password='testpass',
            role='patient'
        )
        
        # Créer fiche basique
        fiche = FicheConsultation.objects.create(
            user=user,
            motif_consultation="Test API",
            status="en_attente"
        )
        
        print(f"✅ Fiche créée: {fiche.id}")
        
        # Nettoyer
        fiche.delete()
        user.delete()
        
        return True
        
    except Exception as e:
        print(f"❌ Création modèle: {e}")
        return False

def main():
    """Tests principaux"""
    print("🚀 Tests API Rapides CI/CD")
    print("=" * 40)
    
    tests = [
        test_basic_api(),
        test_basic_model_creation()
    ]
    
    success_count = sum(tests)
    total_count = len(tests)
    
    print("=" * 40)
    print(f"📊 Résultats: {success_count}/{total_count} tests passés")
    
    if all(tests):
        print("🎉 Tests API rapides: SUCCÈS!")
        sys.exit(0)
    else:
        print("⚠️  Certains tests API échoués")
        sys.exit(1)

if __name__ == "__main__":
    main()