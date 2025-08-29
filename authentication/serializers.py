from rest_framework import serializers

from .models import (
    CustomUser,
    UserProfilePatient,
    UserProfileMedecin,
)

from .models import CustomUser, UserProfilePatient, UserProfileMedecin

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

        fields = ["date_of_birth", "phone_number", "address"]
        read_only_fields = fields

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

        fields = ["specialty", "phone_number", "address"]
        read_only_fields = fields

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
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_login",
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
            "id","is_active","is_staff","is_superuser","date_joined","last_login","patient_profile","medecin_profile"
        ]

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=4)

    class Meta:
        model = CustomUser
        fields = ["username", "password", "email", "role", "first_name", "last_name"]

    def validate_email(self, value):
        if value and CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user
