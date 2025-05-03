import json
import datetime


from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import login

from .forms import FicheConsultationForm


# Vue d'inscription
class RegisterView(FormView):
    template_name = 'chat/register.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)  # Connexion automatique après l'inscription
        messages.success(self.request, "Inscription réussie ! Vous êtes maintenant connecté.")
        return redirect('home')  # Redirige vers la page d'accueil

    def form_invalid(self, form):
        messages.error(self.request, "Une erreur est survenue lors de l'inscription.")
        return super().form_invalid(form)


# Vue de connexion
class CustomLoginView(LoginView):
    template_name = 'chat/login.html'
    redirect_authenticated_user = True

    def form_invalid(self, form):
        messages.error(self.request, "Nom d'utilisateur ou mot de passe incorrect.")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('home')


# Vue de déconnexion
class CustomLogoutView(LogoutView):
    next_page = 'login'


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'chat/home.html'
    login_url = 'login'  # URL de redirection si l'utilisateur n'est pas connecté
    redirect_field_name = 'next'  # Nom du paramètre de requête pour la redirection après connexion


### chat
from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy

import threading
from langchain.schema import HumanMessage

from .llm_config import gpt4, claude, gemini, synthese_llm
from .models import Conversation, MessageIA, FicheConsultation


class AnalyseSymptomesView(LoginRequiredMixin, View):
    template_name = "chat/home.html"

    def get(self, request):
        texte = ""
        # Récupération des symptômes depuis la session
        symptomes_json = request.session.pop("symptomes_diagnostic", None)  # pop supprime et retourne

        if symptomes_json:
            try:
                symptomes_dict = json.loads(symptomes_json)
                texte = formater_symptomes_en_texte(symptomes_dict)
                print("Texte formaté :", texte)
            except (json.JSONDecodeError, TypeError) as e:
                print("Erreur lors du décodage des symptômes :", e)

        # Passage du texte au template pour affichage ou traitement JS
        return render(request, self.template_name, {"symptomes_texte": texte})

    def post(self, request):
        data = json.loads(request.body)
        symptomes = data.get("message")
        message = HumanMessage(content=f"Voici les symptômes du patient : {symptomes}")

        conversation = Conversation.objects.create(user=request.user)

        MessageIA.objects.create(
            conversation=conversation,
            role='user',
            content=symptomes
        )

        results = {}

        def get_gpt4():
            results["gpt4"] = gpt4([message]).content

        def get_claude():
            results["claude"] = claude([message]).content

        def get_gemini():
            results["gemini"] = gemini([message]).content

        threads = [
            threading.Thread(target=get_gpt4),
            threading.Thread(target=get_claude),
            threading.Thread(target=get_gemini),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        MessageIA.objects.create(conversation=conversation, role='gpt4', content=results['gpt4'])
        MessageIA.objects.create(conversation=conversation, role='claude', content=results['claude'])
        MessageIA.objects.create(conversation=conversation, role='gemini', content=results['gemini'])

        synthese_message = HumanMessage(
            content=f"""Trois experts ont donné leurs avis :

            - GPT-4 : {results['gpt4']}
            - Claude 3 : {results['claude']}
            - Gemini Pro : {results['gemini']}

            En te basant sur ces trois avis, donne une conclusion claire, rigoureuse et prudente.
            """
        )
        final_response = synthese_llm([synthese_message])

        MessageIA.objects.create(conversation=conversation, role='synthese', content=final_response.content)

        return JsonResponse({
            "response": final_response.content  # <-- clé attendue côté JS
        })

def formater_symptomes_en_texte(symptomes: dict) -> str:
    # Informations personnelles
    nom = symptomes["Identification"]["Nom complet"]
    age = symptomes["Identification"]["Âge"]
    date_naissance = symptomes["Identification"]["Date de naissance"]
    telephone = symptomes["Identification"]["Téléphone"]

    texte = f"Je m'appelle {nom}, j'ai {age} ans (né le {date_naissance}), mon numéro de téléphone est {telephone}. Voici toutes mes informations médicales. J'ai besoin d'un diagnostic basé sur les détails suivants :\n\n"

    texte += f"Motif de consultation : {symptomes.get('Motif de consultation', '')}\n"
    texte += f"Histoire de la maladie : {symptomes.get('Histoire de la maladie', '')}\n\n"

    texte += "Plaintes :\n"
    for k, v in symptomes.get("Plaintes", {}).items():
        texte += f"- {k} : {'Oui' if v else 'Non'}\n"

    texte += "\nSignes vitaux :\n"
    for k, v in symptomes.get("Signes vitaux", {}).items():
        texte += f"- {k} : {v}\n"

    texte += "\nAntécédents personnels :\n"
    for k, v in symptomes.get("Antécédents personnels", {}).items():
        texte += f"- {k} : {'Oui' if v else 'Non'}\n"

    texte += "\nAntécédents familiaux :\n"
    for k, v in symptomes.get("Antécédents familiaux", {}).items():
        texte += f"- {k} : {'Oui' if v else 'Non'}\n"

    texte += "\nMode de vie :\n"
    for k, v in symptomes.get("Mode de vie", {}).items():
        texte += f"- {k} : {v}\n"

    texte += "\nAllergies :\n"
    for k, v in symptomes.get("Allergies", {}).items():
        texte += f"- {k} : {v}\n"

    texte += "\nTraumatismes :\n"
    for k, v in symptomes.get("Traumatismes", {}).items():
        texte += f"- {k} : {v}\n"

    texte += "\nCapacités :\n"
    for k, v in symptomes.get("Capacités", {}).items():
        texte += f"- {k} : {v}\n"

    texte += "\nExamen clinique :\n"
    for k, v in symptomes.get("Examen clinique", {}).items():
        texte += f"- {k} : {v}\n"

    texte += "\nÉvaluation psychosociale :\n"
    for k, v in symptomes.get("Évaluation psychosociale", {}).items():
        texte += f"- {k} : {v}\n"

    return texte


class FicheConsultationCreateView(LoginRequiredMixin, CreateView):
    model = FicheConsultation
    form_class = FicheConsultationForm
    template_name = "chat/fiche_form.html"
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        print("Formulaire valide :", form.cleaned_data)
        fiche = form.save(commit=False)
        fiche.conversation = Conversation.objects.create(user=self.request.user)
        fiche.save()

        # Construction du dictionnaire des symptômes
        symptomes = {
            "Identification": {
                "Nom complet": fiche.nom,
                "Âge": fiche.age,
                "Date de naissance": fiche.date_naissance,
                "Téléphone": fiche.telephone,
                "État civil": fiche.etat_civil,
                "Occupation": fiche.occupation,
                "Adresse": {
                    "Avenue": fiche.avenue,
                    "Quartier": fiche.quartier,
                    "Commune": fiche.commune,
                },
                "Contact d'urgence": {
                    "Nom": fiche.contact_nom,
                    "Téléphone": fiche.contact_telephone,
                    "Adresse": fiche.contact_adresse,
                },
            },
            "Motif de consultation": fiche.motif_consultation,
            "Histoire de la maladie": fiche.histoire_maladie,
            "Plaintes": {
                "Céphalées": fiche.cephalees,
                "Vertiges": fiche.vertiges,
                "Palpitations": fiche.palpitations,
                "Troubles visuels": fiche.troubles_visuels,
                "Nycturie": fiche.nycturie,
            },
            "Signes vitaux": {
                "Température": fiche.temperature,
                "SpO2": fiche.spo2,
                "Tension artérielle": fiche.tension_arterielle,
                "Pouls": fiche.pouls,
                "Fréquence respiratoire": fiche.frequence_respiratoire,
                "Poids": fiche.poids,
            },
            "Antécédents personnels": {
                "Hypertension": fiche.hypertendu,
                "Diabète": fiche.diabetique,
                "Épilepsie": fiche.epileptique,
                "Troubles du comportement": fiche.trouble_comportement,
                "Gastrite": fiche.gastritique,
                "Autres antécédents": fiche.autres_antecedents,
            },
            "Antécédents familiaux": {
                "Drépanocytose": fiche.familial_drepanocytaire,
                "Diabète": fiche.familial_diabetique,
                "Obésité": fiche.familial_obese,
                "Hypertension": fiche.familial_hypertendu,
                "Troubles du comportement": fiche.familial_trouble_comportement,
                "Lien avec la mère": fiche.lien_mere,
                "Lien avec le père": fiche.lien_pere,
                "Lien avec le frère": fiche.lien_frere,
                "Lien avec la sœur": fiche.lien_soeur,
            },
            "Mode de vie": {
                "Tabac": fiche.tabac,
                "Alcool": fiche.alcool,
                "Activité physique": fiche.activite_physique,
                "Détail de l'activité physique": fiche.activite_physique_detail,
                "Alimentation habituelle": fiche.alimentation_habituelle,
            },
            "Allergies": {
                "Allergie médicamenteuse": fiche.allergie_medicamenteuse,
                "Nom du médicament allergène": fiche.medicament_allergique,
            },
            "Traumatismes": {
                "Événement traumatique": fiche.evenement_traumatique,
                "Traumatisme lié au décès d’un enfant": fiche.trauma_deces_enfant,
                "État général": fiche.etat_general,
            },
            "Capacités": {
                "Capacité physique": fiche.capacite_physique,
                "Score physique": fiche.capacite_physique_score,
                "Capacité psychologique": fiche.capacite_psychologique,
                "Score psychologique": fiche.capacite_psychologique_score,
            },
            "Examen clinique": {
                "État général": fiche.etat,
                "Fièvre": fiche.febrile,
                "Coloration bulbaire": fiche.coloration_bulbaire,
                "Coloration palpébrale": fiche.coloration_palpebrale,
                "Téguments": fiche.tegument,
                "Tête": fiche.tete,
                "Cou": fiche.cou,
                "Paroi thoracique": fiche.paroi_thoracique,
                "Poumons": fiche.poumons,
                "Cœur": fiche.coeur,
                "Épigastre et hypochondres": fiche.epigastre_hypochondres,
                "Péri-ombilical et flancs": fiche.peri_ombilical_flancs,
                "Hypogastre et fosses iliaques": fiche.hypogastre_fosses_iliaques,
                "Membres": fiche.membres,
                "Colonne et bassin": fiche.colonne_bassin,
                "Examen gynécologique": fiche.examen_gynecologique,
            },
            "Évaluation psychosociale": {
                "Préoccupations": fiche.preoccupations,
                "Compréhension": fiche.comprehension,
                "Attentes": fiche.attentes,
                "Engagement": fiche.engagement,
            }
        }

        def default_serializer(obj):
            if isinstance(obj, (datetime.date, datetime.datetime)):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} non sérialisable")

        self.request.session["symptomes_diagnostic"] = json.dumps(symptomes, default=default_serializer)

        return redirect("analyse")
