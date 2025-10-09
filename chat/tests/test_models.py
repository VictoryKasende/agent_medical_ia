"""Unit tests for chat models."""

import random
import time

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from authentication.models import CustomUser
from chat.models import Appointment, Conversation, FicheConsultation, MessageIA


@pytest.mark.unit
class TestFicheConsultation:
    """Unit tests for FicheConsultation model."""

    def test_fiche_creation(self, patient_user):
        """Test creating a fiche consultation."""
        timestamp = int(time.time() * 1000) % 1000000
        random_suffix = random.randint(1000, 9999)

        fiche = FicheConsultation.objects.create(
            numero_dossier=f"TEST-{timestamp:06d}-{random_suffix}",
            user=patient_user,
            nom="Doe",
            postnom="John",
            prenom="Patient",
            date_naissance="1990-01-01",
            age=34,
            sexe="M",
            telephone="+243999999999",
            occupation="Test",
            avenue="Avenue 1",
            quartier="Quarter 1",
            commune="Commune 1",
            contact_nom="Contact",
            contact_telephone="+243888888888",
            contact_adresse="Address",
            etat="Conservé",
            capacite_physique="Top",
            capacite_psychologique="Top",
            febrile="Non",
            coloration_bulbaire="Normale",
            coloration_palpebrale="Normale",
            tegument="Normal",
            motif_consultation="Test motif",
            hypothese_patient_medecin="Test hypothese",
            analyses_proposees="Test analyses",
        )

        assert fiche.id is not None
        assert fiche.user == patient_user
        assert fiche.status == "en_analyse"  # Default status
        assert fiche.sexe == "M"

    def test_fiche_unique_numero_dossier(self, sample_fiche):
        """Test that numero_dossier must be unique."""
        with pytest.raises(IntegrityError):
            FicheConsultation.objects.create(
                numero_dossier=sample_fiche.numero_dossier,  # Duplicate
                nom="Test",
                postnom="Test",
                prenom="Test",
                date_naissance="1990-01-01",
                age=30,
                sexe="F",
                telephone="+243999999999",
                occupation="Test",
                avenue="Test",
                quartier="Test",
                commune="Test",
                contact_nom="Test",
                contact_telephone="+243888888888",
                contact_adresse="Test",
                etat="Conservé",
                capacite_physique="Top",
                capacite_psychologique="Top",
                febrile="Non",
                coloration_bulbaire="Normale",
                coloration_palpebrale="Normale",
                tegument="Normal",
                motif_consultation="Test",
                hypothese_patient_medecin="Test",
                analyses_proposees="Test",
            )

    def test_fiche_status_choices(self, sample_fiche):
        """Test valid status choices."""
        valid_statuses = ["en_analyse", "analyse_terminee", "valide_medecin", "rejete_medecin"]

        for status in valid_statuses:
            sample_fiche.status = status
            sample_fiche.save()
            assert sample_fiche.status == status

    def test_fiche_str_method(self, sample_fiche):
        """Test __str__ method returns expected format."""
        expected = f"Fiche Consultation - {sample_fiche.nom} {sample_fiche.postnom} ({sample_fiche.numero_dossier})"
        assert str(sample_fiche) == expected

    def test_fiche_validation_status(self, sample_fiche, medecin_user):
        """Test fiche validation updates status and dates."""
        sample_fiche.status = "valide_medecin"
        sample_fiche.assigned_medecin = medecin_user
        sample_fiche.date_validation = timezone.now()
        sample_fiche.save()

        assert sample_fiche.status == "valide_medecin"
        assert sample_fiche.assigned_medecin == medecin_user
        assert sample_fiche.date_validation is not None


@pytest.mark.unit
class TestConversation:
    """Unit tests for Conversation model."""

    def test_conversation_creation(self, patient_user, sample_fiche):
        """Test creating a conversation."""
        conv = Conversation.objects.create(user=patient_user, fiche=sample_fiche, nom="Test Conversation")

        assert conv.id is not None
        assert conv.user == patient_user
        assert conv.fiche == sample_fiche
        assert conv.nom == "Test Conversation"

    def test_conversation_titre_property_with_name(self, patient_user):
        """Test titre property returns name when set."""
        conv = Conversation.objects.create(user=patient_user, nom="Named Conversation")

        assert conv.titre == "Named Conversation"

    def test_conversation_titre_property_from_message(self, patient_user):
        """Test titre property extracts from first message."""
        conv = Conversation.objects.create(user=patient_user)
        MessageIA.objects.create(
            conversation=conv, role="user", content="This is a long message that should be truncated to 30 characters"
        )

        titre = conv.titre
        assert len(titre) <= 33  # 30 chars + '...'
        assert titre.endswith("...")

    def test_conversation_str_method(self, patient_user, sample_fiche):
        """Test __str__ method format."""
        conv = Conversation.objects.create(user=patient_user, fiche=sample_fiche)

        expected = f"Conversation #{conv.id} - {patient_user.username} (Fiche {sample_fiche.numero_dossier})"
        assert str(conv) == expected


@pytest.mark.unit
class TestMessageIA:
    """Unit tests for MessageIA model."""

    def test_message_creation(self, patient_user):
        """Test creating an IA message."""
        conv = Conversation.objects.create(user=patient_user)
        msg = MessageIA.objects.create(conversation=conv, role="user", content="Test message content")

        assert msg.id is not None
        assert msg.conversation == conv
        assert msg.role == "user"
        assert msg.content == "Test message content"
        assert msg.timestamp is not None

    def test_message_role_choices(self, patient_user):
        """Test valid role choices."""
        conv = Conversation.objects.create(user=patient_user)
        valid_roles = ["user", "gpt4", "claude", "gemini", "synthese"]

        for role in valid_roles:
            msg = MessageIA.objects.create(conversation=conv, role=role, content="Test")
            assert msg.role == role

    def test_message_ordering(self, patient_user):
        """Test messages are ordered by timestamp."""
        conv = Conversation.objects.create(user=patient_user)

        msg1 = MessageIA.objects.create(conversation=conv, role="user", content="First")
        msg2 = MessageIA.objects.create(conversation=conv, role="gpt4", content="Second")
        msg3 = MessageIA.objects.create(conversation=conv, role="user", content="Third")

        messages = list(conv.messageia_set.all())
        assert messages[0] == msg1
        assert messages[1] == msg2
        assert messages[2] == msg3


@pytest.mark.unit
class TestAppointment:
    """Unit tests for Appointment model."""

    def test_appointment_creation(self, patient_user, medecin_user):
        """Test creating an appointment."""
        start = timezone.now()
        end = start + timezone.timedelta(minutes=30)

        appt = Appointment.objects.create(
            patient=patient_user,
            medecin=medecin_user,
            requested_start=start,
            requested_end=end,
            consultation_mode="presentiel",
            message_patient="Test appointment",
        )

        assert appt.id is not None
        assert appt.patient == patient_user
        assert appt.medecin == medecin_user
        assert appt.status == "pending"  # Default status

    def test_appointment_status_transitions(self, patient_user, medecin_user):
        """Test appointment status transitions."""
        start = timezone.now()
        end = start + timezone.timedelta(minutes=30)

        appt = Appointment.objects.create(
            patient=patient_user,
            medecin=medecin_user,
            requested_start=start,
            requested_end=end,
            consultation_mode="presentiel",
        )

        # Test status transitions
        valid_statuses = ["pending", "confirmed", "declined", "cancelled"]
        for status in valid_statuses:
            appt.status = status
            appt.save()
            assert appt.status == status

    def test_appointment_consultation_mode_choices(self, patient_user, medecin_user):
        """Test valid consultation mode choices."""
        start = timezone.now()
        end = start + timezone.timedelta(minutes=30)

        modes = ["presentiel", "distanciel"]
        for mode in modes:
            appt = Appointment.objects.create(
                patient=patient_user,
                medecin=medecin_user,
                requested_start=start,
                requested_end=end,
                consultation_mode=mode,
            )
            assert appt.consultation_mode == mode

    def test_appointment_str_method(self, patient_user, medecin_user):
        """Test __str__ method format."""
        start = timezone.now()
        end = start + timezone.timedelta(minutes=30)

        appt = Appointment.objects.create(
            patient=patient_user,
            medecin=medecin_user,
            requested_start=start,
            requested_end=end,
            consultation_mode="presentiel",
        )

        expected = f"RDV {appt.id} [{appt.get_status_display()}] {patient_user.username} ↔ Dr {medecin_user.username} ({appt.get_consultation_mode_display()})"
        assert str(appt) == expected
