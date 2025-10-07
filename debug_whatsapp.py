#!/usr/bin/env python
"""
Script de debug WhatsApp - Test direct des notifications
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agent_medical_ia.settings')
django.setup()

from django.core.cache import cache
from chat.models import FicheConsultation
from chat.notification_service import notification_service

def debug_whatsapp():
    print("🔍 DEBUG WHATSAPP NOTIFICATIONS")
    print("=" * 50)
    
    # 1. Configuration Twilio
    print("1. Configuration Twilio:")
    twilio_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
    print(f"   Account SID: {twilio_sid[:8]}...{twilio_sid[-4:] if twilio_sid else 'NON CONFIGURÉ'}")
    print(f"   Auth Token: {'CONFIGURÉ' if os.getenv('TWILIO_AUTH_TOKEN') else 'NON CONFIGURÉ'}")
    print(f"   WhatsApp Number: {os.getenv('TWILIO_WHATSAPP_NUMBER', 'NON CONFIGURÉ')}")
    
    # 2. Fiche de test
    print("\n2. Fiche de test:")
    fiche = FicheConsultation.objects.first()
    if not fiche:
        print("   ❌ Aucune fiche trouvée")
        return
    
    print(f"   Fiche ID: {fiche.id}")
    print(f"   Patient: {fiche.nom} {fiche.prenom}")
    print(f"   Téléphone: {fiche.telephone}")
    
    # 3. Cache d'idempotence
    print("\n3. Cache d'idempotence:")
    cache_key = f"whatsapp_sent_{fiche.telephone}_{fiche.id}"
    cached_value = cache.get(cache_key)
    print(f"   Cache key: {cache_key}")
    print(f"   Cache value: {cached_value or 'AUCUN'}")
    
    # Nettoyer le cache
    cache.delete(cache_key)
    print("   Cache nettoyé ✅")
    
    # 4. Test envoi WhatsApp
    print("\n4. Test envoi WhatsApp:")
    try:
        result = notification_service.send_whatsapp(
            to_number=fiche.telephone,
            message=f"Test WhatsApp - {fiche.nom} {fiche.prenom}",
            force_resend=True
        )
        print(f"   Success: {result.success}")
        print(f"   Message SID: {result.message_sid}")
        print(f"   Error: {result.error}")
        print(f"   Status: {result.status}")
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    debug_whatsapp()