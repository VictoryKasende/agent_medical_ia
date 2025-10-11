"""Pytest configuration and fixtures for chat tests."""

import random
import time

import pytest
from django.conf import settings
from rest_framework.test import APIClient

from authentication.models import CustomUser
from chat.models import FicheConsultation


@pytest.fixture
def api_client():
    """Return an API client instance."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, patient_user):
    """Return an authenticated API client."""
    api_client.force_authenticate(user=patient_user)
    return api_client


@pytest.fixture
def patient_user(db):
    """Create and return a patient user."""
    return CustomUser.objects.create_user(
        username="test_patient",
        email="patient@test.com",
        password="testpass123",
        role="patient",
        first_name="Test",
        last_name="Patient",
    )


@pytest.fixture
def medecin_user(db):
    """Create and return a medecin user."""
    return CustomUser.objects.create_user(
        username="test_medecin",
        email="medecin@test.com",
        password="testpass123",
        role="medecin",
        first_name="Dr",
        last_name="Test",
    )


@pytest.fixture
def admin_user(db):
    """Create and return an admin user."""
    return CustomUser.objects.create_superuser(
        username="test_admin", email="admin@test.com", password="testpass123", role="medecin"
    )


@pytest.fixture
def sample_fiche(db, patient_user):
    """Create and return a sample fiche consultation."""
    timestamp = int(time.time() * 1000) % 1000000
    random_suffix = random.randint(1000, 9999)

    return FicheConsultation.objects.create(
        numero_dossier=f"TEST-{timestamp:06d}-{random_suffix}",
        user=patient_user,
        nom="Doe",
        postnom="Test",
        prenom="John",
        date_naissance="1990-01-01",
        age=34,
        sexe="M",
        telephone="+243999999999",
        occupation="Developer",
        avenue="Test Avenue",
        quartier="Test Quarter",
        commune="Test Commune",
        contact_nom="Emergency Contact",
        contact_telephone="+243888888888",
        contact_adresse="Test Address",
        etat="Conservé",
        capacite_physique="Top",
        capacite_psychologique="Top",
        febrile="Non",
        coloration_bulbaire="Normale",
        coloration_palpebrale="Normale",
        tegument="Normal",
        motif_consultation="Test consultation",
        hypothese_patient_medecin="Test hypothesis",
        analyses_proposees="Test analyses",
        status="en_analyse",
    )


@pytest.fixture
def validated_fiche(sample_fiche, medecin_user):
    """Create and return a validated fiche."""
    sample_fiche.status = "valide_medecin"
    sample_fiche.assigned_medecin = medecin_user
    sample_fiche.diagnostic = "Test diagnostic"
    sample_fiche.traitement = "Test treatment"
    sample_fiche.save()
    return sample_fiche


@pytest.fixture
def disable_celery(settings):
    """Disable Celery for tests."""
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests automatically."""
    pass
