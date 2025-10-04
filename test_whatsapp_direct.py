#!/usr/bin/env python3
import os
import sys
import django

# Configuration Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agent_medical_ia.settings')
django.setup()

from twilio.rest import Client

# Test direct Twilio WhatsApp
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN') 
whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')

print(f"ACCOUNT_SID: {account_sid}")
print(f"AUTH_TOKEN: {'*' * len(auth_token) if auth_token else 'None'}")
print(f"WHATSAPP_NUMBER: {whatsapp_number}")

client = Client(account_sid, auth_token)

# Test d'envoi simple
try:
    message = client.messages.create(
        body="Test direct depuis Python - Agent Médical IA",
        from_=f"whatsapp:{whatsapp_number}",
        to="whatsapp:+243997699393"
    )
    print(f"✅ Message envoyé: SID={message.sid}, Status={message.status}")
except Exception as e:
    print(f"❌ Erreur: {e}")