"""
Tests complets pour les fonctionnalités P1 d'Agent Médical IA.
Couvre les nouveaux modèles, endpoints et permissions.
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import datetime, timedelta, time, date
import json

from chat.models import (
    FicheConsultation, MedecinAvailability, MedecinException, 
    WebhookEvent, DataExportJob, FicheMessage
)

User = get_user_model()


class MedecinAvailabilityModelTests(TestCase):
    """Tests pour le modèle MedecinAvailability."""
    
    def setUp(self):
        self.medecin = User.objects.create_user(
            username='dr_test',
            email='dr@test.com',
            password='test123',
            role='medecin'
        )
    
    def test_create_availability(self):
        """Test création d'une disponibilité."""
        availability = MedecinAvailability.objects.create(
            medecin=self.medecin,
            day_of_week=1,  # Mardi
            start_time=time(9, 0),
            end_time=time(17, 0),
            consultation_type='both',
            duration_minutes=30
        )
        
        self.assertEqual(availability.medecin, self.medecin)
        self.assertEqual(availability.get_day_of_week_display(), 'Mardi')
        self.assertEqual(availability.duration_formatted, '30min')
        self.assertTrue(availability.is_active)
    
    def test_duration_formatted(self):
        """Test formatage de la durée."""
        # 30 minutes
        availability = MedecinAvailability.objects.create(
            medecin=self.medecin,
            day_of_week=1,
            start_time=time(9, 0),
            end_time=time(17, 0),
            duration_minutes=30
        )
        self.assertEqual(availability.duration_formatted, '30min')
        
        # 1 heure
        availability.duration_minutes = 60
        self.assertEqual(availability.duration_formatted, '1h')
        
        # 1h30
        availability.duration_minutes = 90
        self.assertEqual(availability.duration_formatted, '1h30')
    
    def test_unique_constraint(self):
        """Test contrainte d'unicité."""
        # Première disponibilité
        MedecinAvailability.objects.create(
            medecin=self.medecin,
            day_of_week=1,
            start_time=time(9, 0),
            end_time=time(12, 0)
        )
        
        # Tentative de création d'une disponibilité identique
        with self.assertRaises(Exception):
            MedecinAvailability.objects.create(
                medecin=self.medecin,
                day_of_week=1,
                start_time=time(9, 0),
                end_time=time(12, 0)
            )


class WebhookEventModelTests(TestCase):
    """Tests pour le modèle WebhookEvent."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='patient_test',
            email='patient@test.com',
            password='test123',
            role='patient'
        )
    
    def test_create_webhook_event(self):
        """Test création d'un événement webhook."""
        webhook = WebhookEvent.objects.create(
            event_type='whatsapp_incoming',
            external_id='MSG123456',
            sender_phone='+33123456789',
            recipient_phone='+33987654321',
            content='Bonjour, j\'ai une question',
            raw_payload={'test': 'data'}
        )
        
        self.assertEqual(webhook.processing_status, 'pending')
        self.assertEqual(webhook.event_type, 'whatsapp_incoming')
        self.assertIsNotNone(webhook.received_at)
    
    def test_mark_processed(self):
        """Test marquage comme traité."""
        webhook = WebhookEvent.objects.create(
            event_type='sms_incoming',
            external_id='SMS123456',
            sender_phone='+33123456789',
            recipient_phone='+33987654321',
            content='Test message',
            raw_payload={}
        )
        
        webhook.mark_processed()
        
        self.assertEqual(webhook.processing_status, 'processed')
        self.assertIsNotNone(webhook.processed_at)
    
    def test_mark_failed(self):
        """Test marquage comme échoué."""
        webhook = WebhookEvent.objects.create(
            event_type='whatsapp_incoming',
            external_id='MSG123456',
            sender_phone='+33123456789',
            recipient_phone='+33987654321',
            content='Test',
            raw_payload={}
        )
        
        error_message = "Utilisateur introuvable"
        webhook.mark_failed(error_message)
        
        self.assertEqual(webhook.processing_status, 'failed')
        self.assertEqual(webhook.processing_error, error_message)
        self.assertIsNotNone(webhook.processed_at)


class AvailabilityAPITests(APITestCase):
    """Tests API pour les disponibilités médecin."""
    
    def setUp(self):
        # Créer les utilisateurs
        self.medecin = User.objects.create_user(
            username='dr_api',
            email='dr@api.com',
            password='test123',
            role='medecin'
        )
        
        self.patient = User.objects.create_user(
            username='patient_api',
            email='patient@api.com',
            password='test123',
            role='patient'
        )
        
        self.admin = User.objects.create_user(
            username='admin_api',
            email='admin@api.com',
            password='test123',
            is_staff=True
        )
        
        # Créer une disponibilité de test
        self.availability = MedecinAvailability.objects.create(
            medecin=self.medecin,
            day_of_week=1,  # Mardi
            start_time=time(9, 0),
            end_time=time(17, 0),
            consultation_type='both',
            duration_minutes=30,
            location='Cabinet médical'
        )
        
        self.client = APIClient()
    
    def test_medecin_can_list_own_availabilities(self):
        """Test: médecin peut lister ses disponibilités."""
        self.client.force_authenticate(user=self.medecin)
        
        url = reverse('chat_api:availability-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.availability.id)
    
    def test_patient_can_see_active_availabilities(self):
        """Test: patient peut voir les disponibilités actives."""
        self.client.force_authenticate(user=self.patient)
        
        url = reverse('chat_api:availability-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Patient ne voit que les disponibilités actives
        self.assertEqual(len(response.data['results']), 1)
    
    def test_medecin_can_create_availability(self):
        """Test: médecin peut créer une disponibilité."""
        self.client.force_authenticate(user=self.medecin)
        
        data = {
            'day_of_week': 3,  # Jeudi
            'start_time': '14:00:00',
            'end_time': '18:00:00',
            'consultation_type': 'distanciel',
            'duration_minutes': 45,
            'max_consultations': 2
        }
        
        url = reverse('chat_api:availability-list')
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['medecin'], self.medecin.id)
        self.assertEqual(response.data['day_of_week'], 3)
    
    def test_patient_cannot_create_availability(self):
        """Test: patient ne peut pas créer de disponibilité."""
        self.client.force_authenticate(user=self.patient)
        
        data = {
            'medecin': self.medecin.id,
            'day_of_week': 3,
            'start_time': '14:00:00',
            'end_time': '18:00:00'
        }
        
        url = reverse('chat_api:availability-list')
        response = self.client.post(url, data)
        
        # Dépend de la permission configurée
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_405_METHOD_NOT_ALLOWED])
    
    def test_available_slots_endpoint(self):
        """Test endpoint des créneaux disponibles."""
        self.client.force_authenticate(user=self.patient)
        
        # Calculer les dates de test (semaine prochaine)
        today = date.today()
        next_monday = today + timedelta(days=(7 - today.weekday()))
        next_friday = next_monday + timedelta(days=4)
        
        url = reverse('chat_api:availability-available-slots')
        response = self.client.get(url, {
            'date_start': next_monday.strftime('%Y-%m-%d'),
            'date_end': next_friday.strftime('%Y-%m-%d'),
            'medecin': self.medecin.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_calendar_ics_generation(self):
        """Test génération du calendrier ICS."""
        self.client.force_authenticate(user=self.medecin)
        
        url = reverse('chat_api:availability-calendar-ics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/calendar; charset=utf-8')
        self.assertIn('BEGIN:VCALENDAR', response.content.decode())
        self.assertIn('END:VCALENDAR', response.content.decode())


class WebhookAPITests(APITestCase):
    """Tests API pour les webhooks."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='user_webhook',
            email='user@webhook.com',
            password='test123',
            role='patient',
            telephone='+33123456789'
        )
        
        self.medecin = User.objects.create_user(
            username='dr_webhook',
            email='dr@webhook.com',
            password='test123',
            role='medecin'
        )
        
        # Créer une fiche pour associer
        self.fiche = FicheConsultation.objects.create(
            user=self.user,
            nom='Test',
            prenom='Patient',
            age=30,
            sexe='M',
            telephone='+33123456789',
            date_naissance='1994-01-01',
            etat_civil='Célibataire',
            occupation='Test',
            avenue='Test',
            quartier='Test',
            commune='Test',
            contact_nom='Test',
            contact_telephone='+33987654321',
            contact_adresse='Test',
            etat='Conservé',
            febrile='Non',
            coloration_bulbaire='normale',
            coloration_palpebrale='normale'
        )
        
        self.client = APIClient()
    
    def test_twilio_whatsapp_webhook(self):
        """Test webhook Twilio WhatsApp."""
        # Simuler un webhook Twilio
        webhook_data = {
            'MessageSid': 'MSG123456789',
            'From': 'whatsapp:+33123456789',
            'To': 'whatsapp:+33987654321',
            'Body': 'Bonjour, j\'ai une question sur ma consultation'
        }
        
        url = reverse('chat_api:webhook-twilio-whatsapp')
        response = self.client.post(url, webhook_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'received')
        
        # Vérifier que le webhook a été créé
        webhook = WebhookEvent.objects.filter(external_id='MSG123456789').first()
        self.assertIsNotNone(webhook)
        self.assertEqual(webhook.event_type, 'whatsapp_incoming')
        self.assertEqual(webhook.sender_phone, '+33123456789')
    
    def test_twilio_sms_webhook(self):
        """Test webhook Twilio SMS."""
        webhook_data = {
            'MessageSid': 'SMS123456789',
            'From': '+33123456789',
            'To': '+33987654321',
            'Body': 'Question par SMS'
        }
        
        url = reverse('chat_api:webhook-twilio-sms')
        response = self.client.post(url, webhook_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'received')
        
        # Vérifier le webhook créé
        webhook = WebhookEvent.objects.filter(external_id='SMS123456789').first()
        self.assertIsNotNone(webhook)
        self.assertEqual(webhook.event_type, 'sms_incoming')
    
    def test_webhook_user_association(self):
        """Test association automatique utilisateur via webhook."""
        webhook_data = {
            'MessageSid': 'MSG_ASSOC_123',
            'From': 'whatsapp:+33123456789',  # Numéro du user
            'To': 'whatsapp:+33987654321',
            'Body': 'Message test association'
        }
        
        url = reverse('chat_api:webhook-twilio-whatsapp')
        response = self.client.post(url, webhook_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier l'association
        webhook = WebhookEvent.objects.filter(external_id='MSG_ASSOC_123').first()
        self.assertIsNotNone(webhook)
        self.assertEqual(webhook.related_user, self.user)
        self.assertEqual(webhook.related_fiche, self.fiche)
        
        # Vérifier qu'un message a été créé
        self.assertIsNotNone(webhook.created_message)
        self.assertEqual(webhook.created_message.fiche, self.fiche)
        self.assertEqual(webhook.created_message.author, self.user)


class DataExportAPITests(APITestCase):
    """Tests API pour les exports de données."""
    
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin_export',
            email='admin@export.com',
            password='test123',
            is_staff=True
        )
        
        self.user = User.objects.create_user(
            username='user_export',
            email='user@export.com',
            password='test123',
            role='patient'
        )
        
        # Créer quelques fiches de test
        for i in range(3):
            FicheConsultation.objects.create(
                nom=f'Patient{i}',
                prenom='Test',
                age=25 + i,
                sexe='M' if i % 2 == 0 else 'F',
                telephone=f'+3312345678{i}',
                date_naissance=f'199{i}-01-01',
                etat_civil='Célibataire',
                occupation='Test',
                avenue='Test',
                quartier='Test',
                commune='Test',
                contact_nom='Test',
                contact_telephone='+33987654321',
                contact_adresse='Test',
                etat='Conservé',
                febrile='Non',
                coloration_bulbaire='normale',
                coloration_palpebrale='normale',
                motif_consultation=f'Motif test {i}',
                status='valide_medecin' if i < 2 else 'en_analyse'
            )
        
        self.client = APIClient()
    
    def test_admin_can_create_export(self):
        """Test: admin peut créer un export."""
        self.client.force_authenticate(user=self.admin)
        
        data = {
            'export_format': 'csv',
            'date_start': '2024-01-01',
            'date_end': '2024-12-31',
            'include_personal_data': False,
            'filters': {
                'status': ['valide_medecin'],
                'age_min': 20,
                'age_max': 40
            }
        }
        
        url = reverse('chat_api:export-list')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['export_format'], 'csv')
        self.assertEqual(response.data['status'], 'pending')
    
    def test_non_admin_cannot_create_export(self):
        """Test: utilisateur normal ne peut pas créer d'export."""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'export_format': 'json',
            'date_start': '2024-01-01',
            'date_end': '2024-12-31'
        }
        
        url = reverse('chat_api:export-list')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_export_validation(self):
        """Test validation des données d'export."""
        self.client.force_authenticate(user=self.admin)
        
        # Test: date fin avant date début
        data = {
            'export_format': 'csv',
            'date_start': '2024-12-31',
            'date_end': '2024-01-01'
        }
        
        url = reverse('chat_api:export-list')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('date_end', response.data)
    
    def test_export_date_range_limit(self):
        """Test limitation de la plage de dates."""
        self.client.force_authenticate(user=self.admin)
        
        # Test: plage trop grande (plus de 2 ans)
        data = {
            'export_format': 'csv',
            'date_start': '2020-01-01',
            'date_end': '2025-01-01'  # 5 ans
        }
        
        url = reverse('chat_api:export-list')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('date_end', response.data)


class PermissionsTests(APITestCase):
    """Tests des permissions pour tous les nouveaux endpoints."""
    
    def setUp(self):
        self.patient = User.objects.create_user(
            username='patient_perm',
            email='patient@perm.com',
            password='test123',
            role='patient'
        )
        
        self.medecin = User.objects.create_user(
            username='medecin_perm',
            email='medecin@perm.com',
            password='test123',
            role='medecin'
        )
        
        self.admin = User.objects.create_user(
            username='admin_perm',
            email='admin@perm.com',
            password='test123',
            is_staff=True
        )
        
        self.client = APIClient()
    
    def test_availability_permissions(self):
        """Test permissions pour les disponibilités."""
        endpoints = [
            'chat_api:availability-list',
            'chat_api:availability-available-slots'
        ]
        
        for endpoint in endpoints:
            url = reverse(endpoint)
            
            # Test sans authentification - utiliser AnonymousUser
            self.client.logout()
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
            
            # Test avec patient
            self.client.force_authenticate(user=self.patient)
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Test avec médecin
            self.client.force_authenticate(user=self.medecin)
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_export_permissions(self):
        """Test permissions pour les exports."""
        url = reverse('chat_api:export-list')
        
        # Test sans authentification
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test avec patient
        self.client.force_authenticate(user=self.patient)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test avec médecin non-admin
        self.client.force_authenticate(user=self.medecin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test avec admin
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_webhook_public_endpoints(self):
        """Test endpoints publics des webhooks."""
        # Les webhooks Twilio doivent être accessibles sans auth
        endpoints = [
            'chat_api:webhook-twilio-whatsapp',
            'chat_api:webhook-twilio-sms'
        ]
        
        for endpoint in endpoints:
            url = reverse(endpoint)
            response = self.client.post(url, {
                'MessageSid': 'TEST123',
                'From': '+33123456789',
                'To': '+33987654321',
                'Body': 'Test message'
            })
            
            # Doit être accessible sans authentification
            self.assertEqual(response.status_code, status.HTTP_200_OK)


class IntegrationTests(APITestCase):
    """Tests d'intégration pour les workflows complets."""
    
    def setUp(self):
        self.medecin = User.objects.create_user(
            username='dr_integration',
            email='dr@integration.com',
            password='test123',
            role='medecin'
        )
        
        self.patient = User.objects.create_user(
            username='patient_integration',
            email='patient@integration.com',
            password='test123',
            role='patient',
            telephone='+33123456789'
        )
        
        self.client = APIClient()
    
    def test_complete_availability_workflow(self):
        """Test workflow complet des disponibilités."""
        self.client.force_authenticate(user=self.medecin)
        
        # 1. Médecin crée ses disponibilités
        availability_data = {
            'day_of_week': 1,  # Mardi
            'start_time': '09:00:00',
            'end_time': '17:00:00',
            'consultation_type': 'both',
            'duration_minutes': 30,
            'location': 'Cabinet test'
        }
        
        url = reverse('chat_api:availability-list')
        response = self.client.post(url, availability_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        availability_id = response.data['id']
        
        # 2. Patient consulte les créneaux disponibles
        self.client.force_authenticate(user=self.patient)
        
        today = date.today()
        next_week = today + timedelta(days=7)
        
        url = reverse('chat_api:availability-available-slots')
        response = self.client.get(url, {
            'date_start': today.strftime('%Y-%m-%d'),
            'date_end': next_week.strftime('%Y-%m-%d'),
            'medecin': self.medecin.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slots = response.data
        
        # Vérifier qu'on a des créneaux
        available_slots = [slot for slot in slots if slot['available']]
        self.assertGreater(len(available_slots), 0)
        
        # 3. Médecin génère son calendrier ICS
        self.client.force_authenticate(user=self.medecin)
        
        url = reverse('chat_api:availability-calendar-ics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/calendar; charset=utf-8')
    
    def test_webhook_to_message_workflow(self):
        """Test workflow webhook vers création de message."""
        # 1. Créer une fiche pour le patient
        fiche = FicheConsultation.objects.create(
            user=self.patient,
            nom='Test',
            prenom='Integration',
            age=30,
            sexe='M',
            telephone='+33123456789',
            date_naissance='1994-01-01',
            etat_civil='Célibataire',
            occupation='Test',
            avenue='Test',
            quartier='Test',
            commune='Test',
            contact_nom='Test',
            contact_telephone='+33987654321',
            contact_adresse='Test',
            etat='Conservé',
            febrile='Non',
            coloration_bulbaire='normale',
            coloration_palpebrale='normale'
        )
        
        # 2. Simuler un message WhatsApp entrant
        webhook_data = {
            'MessageSid': 'MSG_INTEGRATION_123',
            'From': 'whatsapp:+33123456789',
            'To': 'whatsapp:+33987654321',
            'Body': 'J\'ai une question sur ma consultation'
        }
        
        url = reverse('chat_api:webhook-twilio-whatsapp')
        response = self.client.post(url, webhook_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 3. Vérifier que le webhook a été traité
        webhook = WebhookEvent.objects.filter(external_id='MSG_INTEGRATION_123').first()
        self.assertIsNotNone(webhook)
        self.assertEqual(webhook.related_user, self.patient)
        self.assertEqual(webhook.related_fiche, fiche)
        self.assertEqual(webhook.processing_status, 'processed')
        
        # 4. Vérifier qu'un message a été créé dans la fiche
        message = FicheMessage.objects.filter(
            fiche=fiche,
            author=self.patient,
            content='J\'ai une question sur ma consultation'
        ).first()
        self.assertIsNotNone(message)
        self.assertEqual(webhook.created_message, message)