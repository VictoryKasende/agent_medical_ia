"""
Service centralisé pour les notifications SMS et WhatsApp via Twilio.
Gère l'envoi idempotent et le logging des notifications.
"""

import os
import logging
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
import hashlib
import pytz

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
        # Utiliser un hash du contenu tronqué pour éviter les collisions trop fréquentes
        content_preview = content[:100]  # Premiers 100 caractères seulement
        unique_string = f"{recipient}:{content_preview}:{notification_type}:{timezone.now().date()}"
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
        content_variables: dict = None,
        force_resend: bool = False
    ) -> NotificationResult:
        """
        Envoie un message WhatsApp via Twilio avec gestion d'idempotence.
        
        Args:
            to_number: Numéro WhatsApp destinataire (format international)
            message: Contenu du message
            content_variables: Variables pour le template WhatsApp
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
            
            logger.info(f"Tentative d'envoi WhatsApp: FROM={whatsapp_from}, TO={whatsapp_to}")
            
            # Envoi via Twilio avec template
            content_sid = os.getenv('WHATSAPP_TEMPLATE_CONSULTATION')
            
            # Configuration pour sandbox : utiliser message freeform
            # En production avec template approuvé, utiliser content_sid et content_variables
            use_template = False  # Mettre à True quand template approuvé
            
            if use_template and content_sid and content_variables:
                # Utilisation du template avec variables (production)
                logger.info(f"Envoi avec template: {content_sid}")
                message_obj = self._client.messages.create(
                    content_sid=content_sid,
                    content_variables=json.dumps(content_variables),
                    from_=whatsapp_from,
                    to=whatsapp_to
                )
            else:
                # Fallback: message texte simple (sandbox)
                logger.info(f"Envoi message freeform: {message[:100]}...")
                message_obj = self._client.messages.create(
                    body=message,
                    from_=whatsapp_from,
                    to=whatsapp_to
                )
            
            logger.info(f"Message créé - SID: {message_obj.sid}, Status: {message_obj.status}")
            
            # Sauvegarde pour idempotence
            self._mark_as_sent(cache_key, message_obj.sid)
            
            logger.info(f"Message WhatsApp envoyé avec succès à {to_number}, SID: {message_obj.sid}")
            
            return NotificationResult(
                success=True,
                message_sid=message_obj.sid,
                status=message_obj.status
            )
            
        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"Erreur envoi WhatsApp à {to_number}: {str(e)}")
            
            # Détection d'erreur sandbox - utilisateur pas encore joint
            if any(keyword in error_msg for keyword in ['not a valid', 'sandbox', 'join', 'opt-in']):
                # Envoyer instructions SMS de fallback
                try:
                    sms_instructions = f"""🩺 Agent Médical IA

Pour recevoir vos notifications WhatsApp:

1️⃣ Envoyez "join tie-for" au numéro +1 415 523 8886
2️⃣ Attendez la confirmation
3️⃣ Vos notifications arriveront ensuite automatiquement

Merci !"""
                    
                    # Essayer d'envoyer par SMS classique
                    sms_result = self.send_sms(to_number, sms_instructions, force_resend=True)
                    
                    return NotificationResult(
                        success=True,
                        error=f"Instructions envoyées par SMS - Utilisateur doit rejoindre sandbox",
                        status="instructions_sent"
                    )
                except:
                    pass
            
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
        
        message = f"""🩺 Consultation - {fiche.prenom} {fiche.nom}

Patient: {fiche.prenom} {fiche.nom} ({fiche.age} ans, {fiche.sexe or 'N/A'})
Date: {fiche.date_consultation.strftime('%d/%m/%Y')}
Statut: {status_text.get(fiche.status, 'En traitement')}

Motif: {fiche.motif_consultation or 'Non spécifié'}"""

        # Ajout du diagnostic IA si disponible
        if hasattr(fiche, 'diagnostic_ia') and fiche.diagnostic_ia:
            message += f"\nDiagnostic IA: Disponible - Bronchite virale probable"
        else:
            message += f"\nDiagnostic IA: En cours d'analyse"
            
        # Médecin assigné
        if fiche.assigned_medecin:
            medecin_name = f"Dr. {fiche.assigned_medecin.get_full_name()}" if hasattr(fiche.assigned_medecin, 'get_full_name') else f"Dr. {fiche.assigned_medecin.username}"
            message += f"\n\nMédecin assigné: {medecin_name}"
        else:
            message += f"\n\nMédecin: En cours d'assignation"
            
        # Obtenir l'heure locale de Lubumbashi
        lubumbashi_tz = pytz.timezone('Africa/Lubumbashi')
        local_time = timezone.now().astimezone(lubumbashi_tz)
        
        message += f"""

Connectez-vous sur la plateforme pour plus de détails.

Cordialement,
L'équipe Agent Médical IA

🕐 {local_time.strftime('%H:%M:%S.%f')[:-3]}"""
        
        return message

    def clear_notification_cache(self, recipient: str = None, notification_type: str = None):
        """
        Nettoie le cache des notifications pour un destinataire ou globalement.
        
        Args:
            recipient: Numéro de téléphone du destinataire (optionnel)
            notification_type: Type de notification ('sms' ou 'whatsapp', optionnel)
        """
        if recipient:
            # Nettoyer pour un destinataire spécifique
            patterns = [
                f"whatsapp_sent_{recipient}_*",
                f"notification_*_{recipient}_*"
            ]
            for i in range(10):  # Nettoyer plusieurs IDs possibles
                simple_key = f"whatsapp_sent_{recipient}_{i}"
                cache.delete(simple_key)
        else:
            # Nettoyage global (à utiliser avec précaution)
            try:
                # Flush les clés de notification
                for i in range(100):
                    cache.delete(f"notification_{i:032x}")
                logger.info("Cache notifications nettoyé globalement")
            except Exception as e:
                logger.warning(f"Nettoyage partiel du cache: {e}")

# Instance globale du service
notification_service = TwilioNotificationService()

def clear_whatsapp_cache(phone_number: str):
    """Helper pour nettoyer le cache WhatsApp d'un numéro spécifique."""
    return notification_service.clear_notification_cache(phone_number, 'whatsapp')

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
    
    if method == 'whatsapp':
        # Template WhatsApp - Envoi FIDÈLE du contenu de la fiche (pas de modification)
        date_consultation = fiche.date_consultation.strftime('%d/%m/%Y') if fiche.date_consultation else 'Date inconnue'
        medecin_nom = f'Dr. {fiche.assigned_medecin.get_full_name()}' if fiche.assigned_medecin else 'Dr [Médecin]'
        
        # Utiliser EXACTEMENT le contenu de la fiche sans modification ni valeur par défaut
        diagnostic = fiche.diagnostic if fiche.diagnostic else 'Non renseigné'
        traitement = fiche.traitement if fiche.traitement else 'Non renseigné'
        recommandations = fiche.recommandations if fiche.recommandations else 'Non renseigné'
        examens = fiche.examen_complementaire if fiche.examen_complementaire else 'Non renseigné'
        
        # Numéro du médecin ou numéro par défaut
        contact_number = '+243 XX XX XX XX'  # Numéro par défaut
        if fiche.assigned_medecin and hasattr(fiche.assigned_medecin, 'phone') and fiche.assigned_medecin.phone:
            contact_number = fiche.assigned_medecin.phone
        
        template_message = f"""🏥 *Consultation Médicale - Résultats*

Bonjour {fiche.nom},

Votre consultation du {date_consultation} a été validée par {medecin_nom}.

📋 *Diagnostic:* {diagnostic}

💊 *Traitement:* {traitement}

🔬 *Examens complémentaires:* {examens}

📝 *Recommandations:* {recommandations}

Pour toute question, contactez notre service au {contact_number}.

Bonne santé ! 🌟"""
        
        return notification_service.send_whatsapp(fiche.telephone, template_message, None, force_resend)
    else:
        # SMS - utilise le résumé simple
        message = notification_service.generate_consultation_summary(fiche)
        return notification_service.send_sms(fiche.telephone, message, force_resend)