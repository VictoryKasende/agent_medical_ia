from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import FormView

from .forms import CustomUserCreationForm
from .models import CustomUser


class RegisterView(FormView):
    """
    Vue pour l'inscription des utilisateurs.
    Permet aux utilisateurs de s'inscrire et de se connecter automatiquement après l'inscription.
    """

    template_name = "chat/register.html"
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "Inscription réussie ! Vous êtes maintenant connecté.")
        return redirect("patient_dashboard" if user.role == CustomUser.PATIENT_ROLE else "analyse")

    def form_invalid(self, form):
        print(form.errors)
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"Error in {field}: {error}")
                    messages.error(self.request, f"Erreur dans le champ {field}: {error}")
        else:
            print("Form is invalid but no specific errors found.")
        messages.error(
            self.request, "Une erreur est survenue lors de l'inscription. Veuillez vérifier vos informations."
        )
        return super().form_invalid(form)


class CustomLoginView(LoginView):
    template_name = "chat/login.html"
    redirect_authenticated_user = True

    def form_invalid(self, form):
        messages.error(self.request, "Nom d'utilisateur ou mot de passe incorrect.")
        return super().form_invalid(form)

    def get_success_url(self):
        user = self.request.user
        if user.is_superuser:
            return reverse_lazy("admin:index")
        elif user.role == CustomUser.PATIENT_ROLE:
            return reverse_lazy("patient_dashboard")
        elif user.role == CustomUser.MEDECIN_ROLE:
            return reverse_lazy("analyse")
        return super().get_success_url()


class CustomLogoutView(LogoutView):
    """
    Vue pour la déconnexion des utilisateurs.
    """

    next_page = "login"
