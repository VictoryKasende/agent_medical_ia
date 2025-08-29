from rest_framework import serializers

from .models import (
    CustomUser,
    UserProfilePatient,
    UserProfileMedecin,
)


class UserProfilePatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfilePatient
        fields = [
            "id",
            "date_of_birth",
            "phone_number",
            "address",
        ]
        read_only_fields = ["id"]


class UserProfileMedecinSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfileMedecin
        fields = [
            "id",
            "specialty",
            "phone_number",
            "address",
        ]
        read_only_fields = ["id"]


class CustomUserSerializer(serializers.ModelSerializer):
    patient_profile = UserProfilePatientSerializer(read_only=True)
    medecin_profile = UserProfileMedecinSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "phone",
            "patient_profile",
            "medecin_profile",
        ]
        read_only_fields = [
            "id",
            "patient_profile",
            "medecin_profile",
        ]

    def create(self, validated_data):
        # Allow password creation if provided
        password = validated_data.pop("password", None)
        user = CustomUser(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user
