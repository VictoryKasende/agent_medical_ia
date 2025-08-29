from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from authentication.models import CustomUser
from .models import FicheConsultation
from unittest.mock import patch

class DistanceConsultationsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.medecin = CustomUser.objects.create_user(username='doc', password='pwd123', role='medecin')
        self.patient = CustomUser.objects.create_user(username='pat', password='pwd123', role='patient')
        # Créer quelques fiches
        self.f1 = FicheConsultation.objects.create(
            nom='A', postnom='B', prenom='C', date_naissance='1990-01-01', age=34,
            sexe='M', telephone='+243000000', occupation='Dev', avenue='R1', quartier='Q', commune='C',
            contact_nom='CN', contact_telephone='123', contact_adresse='Adr',
            etat='Conservé', capacite_physique='Top', capacite_psychologique='Top', febrile='Non',
            coloration_bulbaire='Normale', coloration_palpebrale='Normale', tegument='Normal',
            is_patient_distance=True, status='en_analyse'
        )
        self.f2 = FicheConsultation.objects.create(
            nom='X', postnom='Y', prenom='Z', date_naissance='1985-05-05', age=39,
            sexe='F', telephone='+243111111', occupation='Ing', avenue='R2', quartier='Q2', commune='C2',
            contact_nom='CN2', contact_telephone='456', contact_adresse='Adr2',
            etat='Altéré', capacite_physique='Moyen', capacite_psychologique='Moyen', febrile='Oui',
            coloration_bulbaire='Anormale', coloration_palpebrale='Anormale', tegument='Anormal',
            is_patient_distance=True, status='analyse_terminee'
        )

    def auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list_requires_auth(self):
        url = '/api/v1/consultations-distance/'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_medecin_ok(self):
        self.auth(self.medecin)
        resp = self.client.get('/api/v1/consultations-distance/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.json()), 2)

    def test_filter_status(self):
        self.auth(self.medecin)
        resp = self.client.get('/api/v1/consultations-distance/?status=analyse_terminee')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(all(item['status'] == 'analyse_terminee' for item in resp.json()))

    def test_retrieve(self):
        self.auth(self.medecin)
        resp = self.client.get(f'/api/v1/consultations-distance/{self.f1.id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['id'], self.f1.id)

    def test_validate_requires_medecin(self):
        self.auth(self.patient)
        resp = self.client.post(f'/api/v1/consultations-distance/{self.f1.id}/validate/')
        self.assertIn(resp.status_code, (403, 404))  # selon permission globale

    def test_validate_medecin_ok(self):
        self.auth(self.medecin)
        resp = self.client.post(f'/api/v1/consultations-distance/{self.f1.id}/validate/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['status'], 'valide_medecin')

    def test_relancer_medecin(self):
        self.auth(self.medecin)
        # put status to analyse_terminee then relancer
        self.f2.status = 'analyse_terminee'
        self.f2.save()
        resp = self.client.post(f'/api/v1/consultations-distance/{self.f2.id}/relancer/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['status'], 'en_analyse')

    @patch('chat.distance_api_views.send_whatsapp_api', return_value=(True, 'ok'))
    def test_send_whatsapp_ok(self, mock_send):
        self.auth(self.medecin)
        resp = self.client.post(f'/api/v1/consultations-distance/{self.f1.id}/send-whatsapp/')
        self.assertEqual(resp.status_code, 200)
        mock_send.assert_called_once()

    def test_webhook_inbound(self):
        resp = self.client.post('/api/v1/whatsapp/webhook/', data={'event': 'delivered'})
        # webhook public (AllowAny)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('received', resp.json())
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model


class DeprecationBannerTests(TestCase):
	def setUp(self):
		self.client = Client()
		User = get_user_model()
		# Créer un user médecin minimal
		self.user = User.objects.create_user(username='doctor', password='pass', role='medecin')

	def test_deprecation_banner_present_on_consultations_distance(self):
		# Authentification
		self.assertTrue(self.client.login(username='doctor', password='pass'))
		response = self.client.get(reverse('consultations_distance'))
		self.assertEqual(response.status_code, 200)
		# Vérifie injection contextuelle
		self.assertIn('deprecation_info', response.context)
		info = response.context['deprecation_info']
		self.assertIsNotNone(info)
		self.assertTrue(hasattr(info, 'removal_target'))
		# Vérifier que le bandeau est visible dans le HTML (mot-clé du remplacement)
		self.assertIn('template legacy', response.content.decode().lower())
