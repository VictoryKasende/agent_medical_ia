from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from authentication.models import CustomUser
from .models import FicheConsultation, Conversation, MessageIA
from unittest.mock import patch


BASE_FICHE_URL = '/api/v1/fiche-consultation/'


def create_fiche(**overrides):
    base = dict(
        nom='Nom', postnom='Post', prenom='Pre', date_naissance='1990-01-01', age=30,
        sexe='M', telephone='+111', occupation='Occ', avenue='Av', quartier='Q', commune='C',
        contact_nom='CN', contact_telephone='123', contact_adresse='Adr',
        etat='Conservé', capacite_physique='Top', capacite_psychologique='Top', febrile='Non',
        coloration_bulbaire='Normale', coloration_palpebrale='Normale', tegument='Normal',
    )
    base.update(overrides)
    return FicheConsultation.objects.create(**base)


class FicheConsultationDistanceTests(TestCase):
    """Tests de la vue distance via le paramètre ?is_patient_distance=true et alias déprécié."""

    def setUp(self):
        self.client = APIClient()
        self.medecin = CustomUser.objects.create_user(username='doc', password='pwd123', role='medecin')
        self.patient = CustomUser.objects.create_user(username='pat', password='pwd123', role='patient')
        self.f1 = create_fiche(is_patient_distance=True, status='en_analyse')
        self.f2 = create_fiche(is_patient_distance=True, status='analyse_terminee', febrile='Oui')

    def test_list_requires_auth(self):
        r = self.client.get(BASE_FICHE_URL + '?is_patient_distance=true')
        self.assertIn(r.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_list_medecin_ok(self):
        self.client.force_authenticate(self.medecin)
        r = self.client.get(BASE_FICHE_URL + '?is_patient_distance=true')
        self.assertEqual(r.status_code, 200)
        payload = r.json()
        # Gérer pagination éventuelle
        if isinstance(payload, dict) and 'results' in payload:
            data = payload['results']
        else:
            data = payload
        self.assertGreaterEqual(len(data), 2)
        sample = data[0]
        expected_subset = {'id', 'nom', 'prenom', 'age', 'status', 'febrile', 'febrile_bool', 'diagnostic_ia'}
        self.assertTrue(expected_subset.issubset(set(sample.keys())))

    def test_filter_status(self):
        self.client.force_authenticate(self.medecin)
        r = self.client.get(BASE_FICHE_URL + '?is_patient_distance=true&status=analyse_terminee')
        self.assertEqual(r.status_code, 200)
        payload = r.json()
        data = payload['results'] if isinstance(payload, dict) and 'results' in payload else payload
        self.assertTrue(all(item['status'] == 'analyse_terminee' for item in data))

    def test_alias_deprecated_still_functions(self):
        self.client.force_authenticate(self.medecin)
        r = self.client.get('/api/v1/consultations-distance/')
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(len(r.json()), 2)
        # Nouveau: vérifier en-tête de dépréciation
        self.assertEqual(r.headers.get('X-Deprecated'), 'true')


class FicheConsultationCRUDAndActionsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.medecin = CustomUser.objects.create_user(username='doc', password='pwd123', role='medecin')
        self.patient = CustomUser.objects.create_user(username='pat', password='pwd123', role='patient')
        self.fiche = create_fiche(status='analyse_terminee')

    def _create_payload(self):
        return {
            'nom': 'N', 'postnom': 'P', 'prenom': 'R', 'date_naissance': '1995-01-01', 'age': 29,
            'sexe': 'M', 'telephone': '+222', 'occupation': 'X', 'avenue': 'Av', 'quartier': 'Q', 'commune': 'C',
            'contact_nom': 'CN', 'contact_telephone': '123', 'contact_adresse': 'Adr',
            'etat': 'Conservé', 'capacite_physique': 'Top', 'capacite_psychologique': 'Top', 'febrile': 'Non',
            'coloration_bulbaire': 'Normale', 'coloration_palpebrale': 'Normale', 'tegument': 'Normal'
        }

    def test_create_requires_auth(self):
        r = self.client.post(BASE_FICHE_URL, data=self._create_payload(), format='json')
        self.assertIn(r.status_code, (401, 403))

    def test_create_ok(self):
        self.client.force_authenticate(self.patient)
        r = self.client.post(BASE_FICHE_URL, data=self._create_payload(), format='json')
        self.assertEqual(r.status_code, 201)
        self.assertIn('id', r.json())

    def test_retrieve(self):
        self.client.force_authenticate(self.medecin)
        r = self.client.get(f'{BASE_FICHE_URL}{self.fiche.id}/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['id'], self.fiche.id)

    def test_update(self):
        self.client.force_authenticate(self.medecin)
        r = self.client.patch(f'{BASE_FICHE_URL}{self.fiche.id}/', data={'motif_consultation': 'Test'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['motif_consultation'], 'Test')

    def test_delete(self):
        self.client.force_authenticate(self.medecin)
        r = self.client.delete(f'{BASE_FICHE_URL}{self.fiche.id}/')
        self.assertIn(r.status_code, (204, 403))  # dépend des permissions futures

    def test_validate_action(self):
        self.client.force_authenticate(self.medecin)
        r = self.client.post(f'{BASE_FICHE_URL}{self.fiche.id}/validate/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['status'], 'valide_medecin')

    def test_reject_action_requires_comment(self):
        self.client.force_authenticate(self.medecin)
        r = self.client.post(f'{BASE_FICHE_URL}{self.fiche.id}/reject/', data={}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_reject_action_ok(self):
        self.client.force_authenticate(self.medecin)
        r = self.client.post(f'{BASE_FICHE_URL}{self.fiche.id}/reject/', data={'commentaire': 'Incomplet'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['status'], 'rejete_medecin')
        self.assertEqual(r.json()['commentaire_rejet'], 'Incomplet')

    def test_relancer(self):
        self.client.force_authenticate(self.medecin)
        r = self.client.post(f'{BASE_FICHE_URL}{self.fiche.id}/relancer/')
        # 202 attendu
        self.assertEqual(r.status_code, 202)

    def test_send_whatsapp(self):
        self.client.force_authenticate(self.medecin)
        r = self.client.post(f'{BASE_FICHE_URL}{self.fiche.id}/send-whatsapp/')
        self.assertEqual(r.status_code, 200)


class ConversationAndMessageTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(username='u1', password='pwd', role='patient')
        self.med = CustomUser.objects.create_user(username='m1', password='pwd', role='medecin')
        self.client.force_authenticate(self.user)
        # Crée une fiche pour lier conversation si besoin
        self.fiche = create_fiche()

    def test_create_conversation(self):
        r = self.client.post('/api/v1/conversations/', data={'fiche': self.fiche.id}, format='json')
        self.assertEqual(r.status_code, 201)
        cid = r.json()['id']
        # Liste limitée au propriétaire patient
        lr = self.client.get('/api/v1/conversations/')
        self.assertEqual(lr.status_code, 200)
        lpayload = lr.json()
        ldata = lpayload['results'] if isinstance(lpayload, dict) and 'results' in lpayload else lpayload
        self.assertTrue(any(c['id'] == cid for c in ldata))

    def test_conversation_messages_flow(self):
        # créer conv
        c = self.client.post('/api/v1/conversations/', data={'fiche': self.fiche.id}, format='json').json()
        cid = c['id']
        # ajout message
        r1 = self.client.post(f'/api/v1/conversations/{cid}/messages/', data={'content': 'Bonjour'}, format='json')
        self.assertEqual(r1.status_code, 201)
        # list messages
        r2 = self.client.get(f'/api/v1/conversations/{cid}/messages/')
        self.assertEqual(r2.status_code, 200)
        mpayload = r2.json()
        mdata = mpayload['results'] if isinstance(mpayload, dict) and 'results' in mpayload else mpayload
        self.assertGreaterEqual(len(mdata), 1)

    def test_medecin_sees_all_conversations(self):
        # patient crée conversation
        c = self.client.post('/api/v1/conversations/', data={'fiche': self.fiche.id}, format='json').json()
        # auth medecin
        self.client.force_authenticate(self.med)
        r = self.client.get('/api/v1/conversations/')
        self.assertEqual(r.status_code, 200)
        rpayload = r.json()
        rdata = rpayload['results'] if isinstance(rpayload, dict) and 'results' in rpayload else rpayload
        self.assertTrue(any(conv['id'] == c['id'] for conv in rdata))


class IAEndpointsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(username='ia', password='pwd', role='medecin')

    def test_analyse_requires_auth(self):
        r = self.client.post('/api/ia/analyse/', data={'texte': 'Symptomes'}, format='json')
        # Selon config d'auth/throttle/permissions, 401 (non authentifié) ou 403 (auth mais rôle insuffisant)
        self.assertIn(r.status_code, (401, 403))

    def test_analyse_ok(self):
        self.client.force_authenticate(self.user)
        r = self.client.post('/api/ia/analyse/', data={'symptomes': 'Symptomes'}, format='json')
        # selon implémentation: 202 ou 200
        self.assertIn(r.status_code, (200, 202))


