from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, UserProfileMedecin, UserProfilePatient


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_active", "is_staff", "first_name", "last_name")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "email")
    ordering = ("username",)

    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        ("Permissions", {"fields": ("role", "is_active", "is_staff", "groups")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "fields": (
                    "username",
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                    "role",
                    "is_active",
                    "is_staff",
                    "groups",
                )
            },
        ),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("patient_profile", "medecin_profile")


@admin.register(UserProfilePatient)
class UserProfilePatientAdmin(admin.ModelAdmin):
    list_display = ("user", "date_of_birth", "phone_number", "address")
    search_fields = ("user__username", "phone_number")
    ordering = ("user__username",)


@admin.register(UserProfileMedecin)
class UserProfileMedecinAdmin(admin.ModelAdmin):
    list_display = ("user", "specialty", "phone_number", "address")
    search_fields = ("user__username", "specialty", "phone_number")
    ordering = ("user__username",)


# Register your models here.
admin.site.site_header = "Agent Medical IA Administration"
admin.site.site_title = "Agent Medical IA Admin"
admin.site.index_title = "Bienvenue dans l'administration d'Agent Medical IA"
admin.site.empty_value_display = "-vide-"  # Affiche '-vide-' pour les champs vides dans l'admin
admin.site.site_url = None  # Désactive le lien vers le site principal dans l'admin
admin.site.enable_nav_sidebar = False  # Désactive la barre latérale de navigation dans l'admin
