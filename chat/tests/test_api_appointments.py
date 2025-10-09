"""Integration tests for Appointment API endpoints."""

import pytest
from django.utils import timezone
from rest_framework import status

from chat.models import Appointment


@pytest.mark.integration
class TestAppointmentAPI:
    """Integration tests for appointment endpoints."""

    BASE_URL = "/api/v1/appointments/"

    def test_list_appointments_requires_auth(self, api_client):
        """Test that listing appointments requires authentication."""
        response = api_client.get(self.BASE_URL)
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_patient_can_list_own_appointments(self, authenticated_client, patient_user, medecin_user):
        """Test that patient can list their own appointments."""
        # Create appointment
        start = timezone.now()
        end = start + timezone.timedelta(minutes=30)
        Appointment.objects.create(
            patient=patient_user,
            medecin=medecin_user,
            requested_start=start,
            requested_end=end,
            consultation_mode="presentiel",
        )

        response = authenticated_client.get(self.BASE_URL)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        results = data.get("results", data) if isinstance(data, dict) else data
        assert len(results) >= 1

    def test_create_appointment_success(self, authenticated_client, medecin_user):
        """Test creating an appointment successfully."""
        start = timezone.now() + timezone.timedelta(days=1)
        end = start + timezone.timedelta(minutes=30)

        payload = {
            "medecin": medecin_user.id,
            "requested_start": start.isoformat(),
            "requested_end": end.isoformat(),
            "consultation_mode": "presentiel",
            "message_patient": "Test appointment message",
        }

        response = authenticated_client.post(self.BASE_URL, data=payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["medecin"] == medecin_user.id
        assert data["consultation_mode"] == "presentiel"
        assert data["status"] == "pending"

    def test_create_appointment_without_medecin(self, authenticated_client):
        """Test creating appointment without medecin (patient field auto-filled)."""
        start = timezone.now() + timezone.timedelta(days=1)
        end = start + timezone.timedelta(minutes=30)

        payload = {
            "requested_start": start.isoformat(),
            "requested_end": end.isoformat(),
            "consultation_mode": "distanciel",
            "message_patient": "Test message",
        }

        response = authenticated_client.post(self.BASE_URL, data=payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["patient"] is not None
        assert data["medecin"] is None

    def test_create_appointment_invalid_dates(self, authenticated_client, medecin_user):
        """Test that end date must be after start date."""
        start = timezone.now() + timezone.timedelta(days=1)
        end = start - timezone.timedelta(minutes=30)  # Invalid: end before start

        payload = {
            "medecin": medecin_user.id,
            "requested_start": start.isoformat(),
            "requested_end": end.isoformat(),
            "consultation_mode": "presentiel",
        }

        response = authenticated_client.post(self.BASE_URL, data=payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_retrieve_appointment(self, authenticated_client, patient_user, medecin_user):
        """Test retrieving a specific appointment."""
        start = timezone.now()
        end = start + timezone.timedelta(minutes=30)

        appt = Appointment.objects.create(
            patient=patient_user,
            medecin=medecin_user,
            requested_start=start,
            requested_end=end,
            consultation_mode="presentiel",
        )

        response = authenticated_client.get(f"{self.BASE_URL}{appt.id}/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["id"] == appt.id
        assert data["patient"] == patient_user.id

    def test_update_appointment(self, authenticated_client, patient_user, medecin_user):
        """Test updating an appointment."""
        start = timezone.now()
        end = start + timezone.timedelta(minutes=30)

        appt = Appointment.objects.create(
            patient=patient_user,
            medecin=medecin_user,
            requested_start=start,
            requested_end=end,
            consultation_mode="presentiel",
            message_patient="Original message",
        )

        response = authenticated_client.patch(
            f"{self.BASE_URL}{appt.id}/", data={"message_patient": "Updated message"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message_patient"] == "Updated message"

    def test_cancel_appointment(self, authenticated_client, patient_user, medecin_user):
        """Test cancelling an appointment."""
        start = timezone.now()
        end = start + timezone.timedelta(minutes=30)

        appt = Appointment.objects.create(
            patient=patient_user,
            medecin=medecin_user,
            requested_start=start,
            requested_end=end,
            consultation_mode="presentiel",
        )

        response = authenticated_client.post(
            f"{self.BASE_URL}{appt.id}/cancel/", data={"message": "Cancelled by patient"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "cancelled"

    def test_patient_cannot_access_others_appointments(self, api_client, patient_user, medecin_user):
        """Test that patient cannot access other patients' appointments."""
        # Create another patient
        other_patient = patient_user.__class__.objects.create_user(
            username="other_patient", password="testpass123", role="patient"
        )

        # Create appointment for other patient
        start = timezone.now()
        end = start + timezone.timedelta(minutes=30)
        appt = Appointment.objects.create(
            patient=other_patient,
            medecin=medecin_user,
            requested_start=start,
            requested_end=end,
            consultation_mode="presentiel",
        )

        # Authenticate as first patient
        api_client.force_authenticate(user=patient_user)

        # Try to access other patient's appointment
        response = api_client.get(f"{self.BASE_URL}{appt.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.integration
class TestAppointmentMedecinActions:
    """Integration tests for medecin-specific appointment actions."""

    BASE_URL = "/api/v1/appointments/"

    def test_medecin_can_confirm_appointment(self, api_client, patient_user, medecin_user):
        """Test that medecin can confirm an appointment."""
        start = timezone.now() + timezone.timedelta(days=1)
        end = start + timezone.timedelta(minutes=30)

        appt = Appointment.objects.create(
            patient=patient_user,
            medecin=medecin_user,
            requested_start=start,
            requested_end=end,
            consultation_mode="presentiel",
        )

        api_client.force_authenticate(user=medecin_user)

        confirmed_start = start + timezone.timedelta(hours=1)
        confirmed_end = confirmed_start + timezone.timedelta(minutes=30)

        response = api_client.post(
            f"{self.BASE_URL}{appt.id}/confirm/",
            data={
                "confirmed_start": confirmed_start.isoformat(),
                "confirmed_end": confirmed_end.isoformat(),
                "message_medecin": "Confirmed",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "confirmed"

    def test_medecin_can_decline_appointment(self, api_client, patient_user, medecin_user):
        """Test that medecin can decline an appointment."""
        start = timezone.now()
        end = start + timezone.timedelta(minutes=30)

        appt = Appointment.objects.create(
            patient=patient_user,
            medecin=medecin_user,
            requested_start=start,
            requested_end=end,
            consultation_mode="presentiel",
        )

        api_client.force_authenticate(user=medecin_user)

        response = api_client.post(
            f"{self.BASE_URL}{appt.id}/decline/", data={"message_medecin": "Not available"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "declined"
