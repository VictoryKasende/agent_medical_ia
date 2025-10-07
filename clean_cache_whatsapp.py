#!/usr/bin/env python
"""
Script pour nettoyer le cache et diagnostiquer les problèmes WhatsApp
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agent_medical_ia.settings')
django.setup()

from chat.models import FicheConsultation
from chat.notification_service import send_consultation_notification
from django.core.cache import cache
import hashlib
from django.utils import timezone

def clean_cache_and_test():
    print("🔍 DIAGNOSTIC CACHE WHATSAPP")
    print("=" * 50)
    
    fiche = FicheConsultation.objects.first()
    if not fiche:
        print("❌ Aucune fiche trouvée")
        return
        
    phone = fiche.telephone
    print(f"📱 Téléphone: {phone}")
    
    # 1. Nettoyer toutes les clés de cache possibles
    print("\n🧹 NETTOYAGE CACHE:")
    
    # Clé simple
    simple_key = f"whatsapp_sent_{phone}_{fiche.id}"
    if cache.get(simple_key):
        cache.delete(simple_key)
        print(f"✅ Supprimé: {simple_key}")
    
    # Clés avec hash pour différents contenus
    test_contents = [
        "test message",
        "🏥 *Consultation Médicale - Résultats*",
        f"Bonjour {fiche.nom}",
        "Template consultation envoyé"
    ]
    
    for content in test_contents:
        unique_string = f"{phone}:{content}:whatsapp:{timezone.now().date()}"
        hash_key = f"notification_{hashlib.md5(unique_string.encode()).hexdigest()}"
        if cache.get(hash_key):
            cache.delete(hash_key)
            print(f"✅ Supprimé: {hash_key[:30]}...")
    
    # Nettoyer le cache Redis complètement pour les notifications
    try:
        # Flush toutes les clés notification_*
        cache.delete_many([f"notification_{i}" for i in range(1000)])
        cache.delete_many([f"whatsapp_sent_{phone}_{i}" for i in range(10)])
        print("✅ Cache notification nettoyé")
    except:
        print("⚠️ Nettoyage partiel du cache")
    
    # 2. Test d'envoi direct
    print(f"\n📤 TEST ENVOI DIRECT:")
    try:
        result = send_consultation_notification(
            fiche=fiche,
            method='whatsapp',
            force_resend=True
        )
        print(f"Success: {result.success}")
        print(f"Message SID: {result.message_sid}")
        print(f"Error: {result.error}")
        print(f"Status: {result.status}")
        
        if result.success and result.message_sid:
            print("✅ Message envoyé avec succès!")
        else:
            print("❌ Problème d'envoi détecté")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi: {e}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    clean_cache_and_test()