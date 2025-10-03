#!/usr/bin/env python
"""
Test de vérification post-installation pour CI/CD
Vérifie que les dépendances critiques sont bien installées
"""

import sys
import os
import django
from django.conf import settings

def test_django_setup():
    """Test que Django démarre correctement"""
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agent_medical_ia.settings_test')
        django.setup()
        print("✅ Django setup OK")
        return True
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        return False

def test_dependencies():
    """Test des dépendances critiques"""
    tests = []
    
    # Test Django
    try:
        import django
        print(f"✅ Django {django.get_version()}")
        tests.append(True)
    except ImportError as e:
        print(f"❌ Django: {e}")
        tests.append(False)
    
    # Test DRF
    try:
        import rest_framework
        print("✅ Django REST Framework")
        tests.append(True)
    except ImportError as e:
        print(f"❌ Django REST Framework: {e}")
        tests.append(False)
    
    # Test Celery
    try:
        import celery
        print("✅ Celery")
        tests.append(True)
    except ImportError as e:
        print(f"❌ Celery: {e}")
        tests.append(False)
    
    # Test PDF (WeasyPrint ou ReportLab)
    pdf_available = False
    try:
        import weasyprint
        print("✅ WeasyPrint (PDF premium)")
        pdf_available = True
    except ImportError:
        try:
            import reportlab
            print("✅ ReportLab (PDF basic)")
            pdf_available = True
        except ImportError:
            print("⚠️  Aucune bibliothèque PDF disponible")
    
    tests.append(pdf_available)
    
    # Test Pandas (P1)
    try:
        import pandas
        print("✅ Pandas")
        tests.append(True)
    except ImportError as e:
        print(f"❌ Pandas: {e}")
        tests.append(False)
    
    # Test Twilio
    try:
        import twilio
        print("✅ Twilio")
        tests.append(True)
    except ImportError as e:
        print(f"❌ Twilio: {e}")
        tests.append(False)
    
    return all(tests)

def test_models():
    """Test que les modèles Django se chargent"""
    try:
        from chat.models import FicheConsultation, LabResult, FicheAttachment
        print("✅ Modèles Django importés")
        return True
    except Exception as e:
        print(f"❌ Import modèles: {e}")
        return False

def main():
    """Test principal"""
    print("🧪 Tests post-installation CI/CD")
    print("=" * 40)
    
    tests = [
        test_django_setup(),
        test_dependencies(),
        test_models()
    ]
    
    success_count = sum(tests)
    total_count = len(tests)
    
    print("=" * 40)
    print(f"📊 Résultats: {success_count}/{total_count} tests passés")
    
    if all(tests):
        print("🎉 Tous les tests passent!")
        sys.exit(0)
    else:
        print("❌ Certains tests échouent")
        sys.exit(1)

if __name__ == "__main__":
    main()