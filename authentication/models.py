from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from django.db.models.signals import post_save, pre_delete

class CustomUser(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    """

    PATIENT_ROLE = 'patient'
    MEDECIN_ROLE = 'medecin'

    ROLE_CHOICES = [
        (PATIENT_ROLE, 'Patient'),
        (MEDECIN_ROLE, 'Médecin'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')
    email = models.EmailField(blank=True, null=True)

    REQUIRED_FIELDS = ['role']

    def __str__(self):
        return self.username
    
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        """
        Override save method to ensure the user is always in the 'patients' group.
        """
        if self.role == self.PATIENT_ROLE:
            patients_group, created = Group.objects.get_or_create(name='patients')
            self.groups.add(patients_group)
        elif self.role == self.MEDECIN_ROLE:   
            medecins_group, created = Group.objects.get_or_create(name='medecins')
            self.groups.add(medecins_group)
        

class UserProfilePatient(models.Model):
    """
    Profile model for patients, linked to CustomUser.
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='patient_profile')
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"
    
class UserProfileMedecin(models.Model):
    """
    Profile model for doctors, linked to CustomUser.
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='medecin_profile')
    specialty = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)

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
    if instance.role == CustomUser.PATIENT_ROLE:
        instance.patient_profile.delete()
    elif instance.role == CustomUser.MEDECIN_ROLE:
        instance.medecin_profile.delete()

pre_delete.connect(delete_user_profile, sender=CustomUser)
