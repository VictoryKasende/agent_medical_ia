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
