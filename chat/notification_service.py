"""
Service centralisé pour les notifications SMS et WhatsApp via Twilio.
Gère l'envoi idempotent et le logging des notifications.
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
import hashlib

# Configuration du logging
logger = logging.getLogger(__name__)

@dataclass
class NotificationResult:
    """Résultat d'envoi de notification."""
    success: bool
    message_sid: Optional[str] = None
    error: Optional[str] = None
    status: Optional[str] = None

class TwilioNotificationService:
    """Service de notification via Twilio pour SMS et WhatsApp."""
    
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
        
        # Vérification de la configuration
        if not all([self.account_sid, self.auth_token]):
            logger.warning("Configuration Twilio incomplète")
            self._client = None
        else:
            try:
                from twilio.rest import Client
                self._client = Client(self.account_sid, self.auth_token)
            except ImportError:
                logger.error("Twilio SDK non installé. Installer avec: pip install twilio")
                self._client = None
    
    def is_configured(self) -> bool:
        """Vérifie si le service est correctement configuré."""
        return self._client is not None
    
    def _generate_cache_key(self, recipient: str, content: str, notification_type: str) -> str:
        """Génère une clé de cache pour l'idempotence."""
        unique_string = f"{recipient}:{content}:{notification_type}:{timezone.now().date()}"
        return f"notification_{hashlib.md5(unique_string.encode()).hexdigest()}"
    
    def _is_already_sent(self, cache_key: str) -> bool:
        """Vérifie si la notification a déjà été envoyée aujourd'hui."""
        return cache.get(cache_key) is not None
    
    def _mark_as_sent(self, cache_key: str, message_sid: str):
        """Marque la notification comme envoyée (cache 24h)."""
        cache.set(cache_key, message_sid, timeout=86400)  # 24 heures
    
    def send_sms(
        self, 
        to_number: str, 
        message: str, 
        force_resend: bool = False
    ) -> NotificationResult:
        """
        Envoie un SMS via Twilio avec gestion d'idempotence.
        
        Args:
            to_number: Numéro de téléphone destinataire (format international)
            message: Contenu du message
            force_resend: Force l'envoi même si déjà envoyé aujourd'hui
            
        Returns:
            NotificationResult avec le résultat de l'envoi
        """
        if not self.is_configured():
            return NotificationResult(
                success=False,
                error="Service Twilio non configuré"
            )
        
        if not self.phone_number:
            return NotificationResult(
                success=False,
                error="Numéro Twilio SMS non configuré"
            )
        
        # Vérification idempotence
        cache_key = self._generate_cache_key(to_number, message, "sms")
        if not force_resend and self._is_already_sent(cache_key):
            logger.info(f"SMS déjà envoyé aujourd'hui à {to_number}")
            return NotificationResult(
                success=True,
                message_sid=cache.get(cache_key),
                status="already_sent"
            )
        
        try:
            # Formatage du numéro
            if not to_number.startswith('+'):
                to_number = f"+{to_number}"
            
            # Envoi via Twilio
            message_obj = self._client.messages.create(
                body=message,
                from_=self.phone_number,
                to=to_number
            )
            
            # Sauvegarde pour idempotence
            self._mark_as_sent(cache_key, message_obj.sid)
            
            logger.info(f"SMS envoyé avec succès à {to_number}, SID: {message_obj.sid}")
            
            return NotificationResult(
                success=True,
                message_sid=message_obj.sid,
                status=message_obj.status
            )
            
        except Exception as e:
            logger.error(f"Erreur envoi SMS à {to_number}: {str(e)}")
            return NotificationResult(
                success=False,
                error=str(e)
            )
    
    def send_whatsapp(
        self, 
        to_number: str, 
        message: str, 
        force_resend: bool = False
    ) -> NotificationResult:
        """
        Envoie un message WhatsApp via Twilio avec gestion d'idempotence.
        
        Args:
            to_number: Numéro WhatsApp destinataire (format international)
            message: Contenu du message
            force_resend: Force l'envoi même si déjà envoyé aujourd'hui
            
        Returns:
            NotificationResult avec le résultat de l'envoi
        """
        if not self.is_configured():
            return NotificationResult(
                success=False,
                error="Service Twilio non configuré"
            )
        
        if not self.whatsapp_number:
            return NotificationResult(
                success=False,
                error="Numéro Twilio WhatsApp non configuré"
            )
        
        # Vérification idempotence
        cache_key = self._generate_cache_key(to_number, message, "whatsapp")
        if not force_resend and self._is_already_sent(cache_key):
            logger.info(f"Message WhatsApp déjà envoyé aujourd'hui à {to_number}")
            return NotificationResult(
                success=True,
                message_sid=cache.get(cache_key),
                status="already_sent"
            )
        
        try:
            # Formatage des numéros WhatsApp
            if not to_number.startswith('+'):
                to_number = f"+{to_number}"
            
            whatsapp_to = f"whatsapp:{to_number}"
            whatsapp_from = f"whatsapp:{self.whatsapp_number}"
            
            # Envoi via Twilio
            message_obj = self._client.messages.create(
                body=message,
                from_=whatsapp_from,
                to=whatsapp_to
            )
            
            # Sauvegarde pour idempotence
            self._mark_as_sent(cache_key, message_obj.sid)
            
            logger.info(f"Message WhatsApp envoyé avec succès à {to_number}, SID: {message_obj.sid}")
            
            return NotificationResult(
                success=True,
                message_sid=message_obj.sid,
                status=message_obj.status
            )
            
        except Exception as e:
            logger.error(f"Erreur envoi WhatsApp à {to_number}: {str(e)}")
            return NotificationResult(
                success=False,
                error=str(e)
            )
    
    def generate_consultation_summary(self, fiche) -> str:
        """
        Génère un résumé de consultation pour notification patient.
        
        Args:
            fiche: Instance de FicheConsultation
            
        Returns:
            str: Message formaté pour notification
        """
        status_text = {
            'en_analyse': 'en cours d\'analyse par l\'IA',
            'analyse_terminee': 'analysée par l\'IA, en attente de validation médicale',
            'valide_medecin': 'validée par le médecin',
            'rejete_medecin': 'nécessite des informations complémentaires'
        }
        
        message = f"""🏥 Agent Médical IA - Consultation #{fiche.numero_dossier}

Bonjour {fiche.prenom} {fiche.nom},

Votre consultation du {fiche.date_consultation.strftime('%d/%m/%Y')} est {status_text.get(fiche.status, 'en traitement')}.

"""
        
        if fiche.status == 'valide_medecin' and fiche.diagnostic:
            message += f"Diagnostic: {fiche.diagnostic[:200]}{'...' if len(fiche.diagnostic) > 200 else ''}\n\n"
        
        if fiche.status == 'rejete_medecin' and fiche.commentaire_rejet:
            message += f"Informations demandées: {fiche.commentaire_rejet[:200]}{'...' if len(fiche.commentaire_rejet) > 200 else ''}\n\n"
        
        message += "Connectez-vous sur la plateforme pour plus de détails.\n\nCordialement,\nL'équipe Agent Médical IA"
        
        return message

# Instance globale du service
notification_service = TwilioNotificationService()

def send_consultation_notification(fiche, method: str = 'sms', force_resend: bool = False) -> NotificationResult:
    """
    Fonction helper pour envoyer une notification de consultation.
    
    Args:
        fiche: Instance de FicheConsultation
        method: 'sms' ou 'whatsapp'
        force_resend: Force l'envoi même si déjà envoyé
        
    Returns:
        NotificationResult
    """
    if not fiche.telephone:
        return NotificationResult(
            success=False,
            error="Numéro de téléphone non renseigné"
        )
    
    message = notification_service.generate_consultation_summary(fiche)
    
    if method == 'whatsapp':
        return notification_service.send_whatsapp(fiche.telephone, message, force_resend)
    else:
        return notification_service.send_sms(fiche.telephone, message, force_resend)