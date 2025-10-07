from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.db.models.signals import post_save, pre_delete


class UserRole(models.TextChoices):
    PATIENT = "patient", "Patient"
    MEDECIN = "medecin", "Médecin"


class CustomUser(AbstractUser):
    """Custom User model extending Django's AbstractUser."""

    # Backward-compatible constants for existing code paths
    PATIENT_ROLE = UserRole.PATIENT
    MEDECIN_ROLE = UserRole.MEDECIN

    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.PATIENT)
    phone = models.CharField(max_length=20, blank=True, null=True)

    email = models.EmailField(blank=True, null=True)

    REQUIRED_FIELDS = ["role"]

    """  # Corrige les conflits de noms
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='customuser_set',  # Change le nom
        related_query_name='customuser',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='customuser_set',  # Change le nom
        related_query_name='customuser',
    ) """

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        """
        Override save method to ensure the user is always in the correct group.
        """
        if self.role == self.PATIENT_ROLE:
            patients_group, created = Group.objects.get_or_create(name="patients")
            self.groups.add(patients_group)
        elif self.role == self.MEDECIN_ROLE:
            medecins_group, created = Group.objects.get_or_create(name="medecins")
            self.groups.add(medecins_group)


class UserProfilePatient(models.Model):
    """
    Profile model for patients, linked to CustomUser.
    """

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="patient_profile")
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"


class UserProfileMedecin(models.Model):
    """
    Profile model for doctors, linked to CustomUser.
    """

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="medecin_profile")
    specialty = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    is_available = models.BooleanField(
        default=True, help_text="Le médecin est-il disponible pour de nouveaux patients ?"
    )

    def __str__(self):
        return f"Profile of Dr. {self.user.username}"


def create_user_profile(sender, instance, created, **kwargs):
    """
    Create a user profile when a CustomUser is created.
    """
    if created:
        if instance.role == CustomUser.PATIENT_ROLE:
            UserProfilePatient.objects.create(user=instance)
        elif instance.role == CustomUser.MEDECIN_ROLE:
            UserProfileMedecin.objects.create(user=instance)


post_save.connect(create_user_profile, sender=CustomUser)


def delete_user_profile(sender, instance, **kwargs):
    """
    Delete the user profile when a CustomUser is deleted.
    """
    if instance.role == CustomUser.PATIENT_ROLE and hasattr(instance, "patient_profile"):
        instance.patient_profile.delete()
    elif instance.role == CustomUser.MEDECIN_ROLE and hasattr(instance, "medecin_profile"):
        instance.medecin_profile.delete()


pre_delete.connect(delete_user_profile, sender=CustomUser)
