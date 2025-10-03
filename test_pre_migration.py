"""
Test rapide de validation pré-migration pour CI/CD
"""
import os
import sys
import django

def test_settings_loading():
    """Test que les settings se chargent correctement"""
    try:
        # Set settings module
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agent_medical_ia.settings_test')
        
        # Test import settings
        from django.conf import settings
        print(f"✅ Settings chargés: {settings.DJANGO_SETTINGS_MODULE}")
        
        # Test database config
        db_engine = settings.DATABASES['default']['ENGINE']
        print(f"✅ Base de données: {db_engine}")
        
        return True
    except Exception as e:
        print(f"❌ Erreur settings: {e}")
        return False

def test_apps_config():
    """Test que les apps Django se configurent"""
    try:
        # Setup Django
        django.setup()
        
        # Test apps loading
        from django.apps import apps
        installed_apps = [app.name for app in apps.get_app_configs()]
        print(f"✅ Apps Django chargées: {len(installed_apps)} apps")
        
        # Test specific apps
        required_apps = ['chat', 'authentication', 'rest_framework']
        for app in required_apps:
            if app in installed_apps:
                print(f"✅ App {app}: OK")
            else:
                print(f"❌ App {app}: MANQUANTE")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Erreur apps: {e}")
        return False

def test_imports():
    """Test imports critiques"""
    try:
        # Test models import
        from chat.models import FicheConsultation
        print("✅ Modèles Django: OK")
        
        # Test views import  
        from chat import api_views
        print("✅ API Views: OK")
        
        # Test serializers
        from chat import serializers
        print("✅ Serializers: OK")
        
        return True
    except Exception as e:
        print(f"❌ Erreur imports: {e}")
        return False

def main():
    print("🧪 Test validation pré-migration")
    print("=" * 40)
    
    tests = [
        test_settings_loading(),
        test_apps_config(), 
        test_imports()
    ]
    
    success = all(tests)
    print("=" * 40)
    
    if success:
        print("🎉 Tous les tests passent - prêt pour migrations!")
        sys.exit(0)
    else:
        print("❌ Erreurs détectées - arrêt")
        sys.exit(1)

if __name__ == "__main__":
    main()