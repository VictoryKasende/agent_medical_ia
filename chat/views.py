import json
import datetime
import hashlib
import json
import hashlib

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
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.core.cache import cache
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.cache import cache
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from .forms import FicheConsultationForm
from .models import Conversation, MessageIA, FicheConsultation
from .tasks import analyse_symptomes_task


def stream_synthese(synthese_llm, synthese_message):
    """Générateur qui yield les tokens au fur et à mesure via Langchain streaming."""
    for chunk in synthese_llm.stream([synthese_message]):
        # chaque chunk est un ChatMessage dans Langchain
        if hasattr(chunk, 'content'):
            yield chunk.content


class RegisterView(FormView):
    """
    Vue pour l'inscription des utilisateurs.
    Permet aux utilisateurs de s'inscrire et de se connecter automatiquement après l'inscription.
    """
    template_name = 'chat/register.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user) 
        messages.success(self.request, "Inscription réussie ! Vous êtes maintenant connecté.")
        return redirect('home') 

    def form_invalid(self, form):
        messages.error(self.request, "Une erreur est survenue lors de l'inscription.")
        return super().form_invalid(form)


class CustomLoginView(LoginView):
    template_name = 'chat/login.html'
    redirect_authenticated_user = True

    def form_invalid(self, form):
        messages.error(self.request, "Nom d'utilisateur ou mot de passe incorrect.")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('home')


class CustomLogoutView(LogoutView):
    """
    Vue pour la déconnexion des utilisateurs.
    """
    next_page = 'login'


class HomeView(LoginRequiredMixin, TemplateView):
    """Vue d'accueil pour les utilisateurs connectés."""
    template_name = 'chat/home.html'
    login_url = 'login'  
    redirect_field_name = 'next'  


@method_decorator(csrf_exempt, name='dispatch')
class AnalyseSymptomesView(LoginRequiredMixin, View):

    template_name = "chat/home.html"

    def get(self, request):
        texte = ""
        symptomes_json = request.session.pop("symptomes_diagnostic", None)
        if symptomes_json:
            try:
                symptomes_dict = json.loads(symptomes_json)
                texte = formater_symptomes_en_texte(symptomes_dict)
            except (json.JSONDecodeError, TypeError) as e:
                print("Erreur lors du décodage des symptômes :", e)
        user = request.user
        conversations = Conversation.objects.filter(user=user).order_by('id')
        chat_items = []
        for conv in conversations:
            messages = MessageIA.objects.filter(
                conversation=conv,
                role__in=['user', 'synthese']
            ).order_by('id')
            if messages.exists():
                chat_items.append({
                    "conversation": conv,
                    "messages": messages
                })
        context = {
            "symptomes_texte": texte,
            "chat_items": chat_items
        }
        return render(request, self.template_name, context)

    def post(self, request):
        data = json.loads(request.body)
        message_text = data.get("message")
        conversation_id = data.get("conversation_id")

        if conversation_id:
            conversation = Conversation.objects.get(id=conversation_id)
        else:
            conversation = Conversation.objects.create(user=request.user)

        MessageIA.objects.create(
            conversation=conversation,
            role='user',
            content=message_text
        )

        # Création de la clé de cache
        hash_key = hashlib.md5(message_text.encode("utf-8")).hexdigest()
        cache_key = f"diagnostic_{hash_key}"

        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse({"status": "done", "response": cached_result})

        def run_task():
            analyse_symptomes_task.delay(message_text, request.user.id, conversation.id, cache_key)

        transaction.on_commit(run_task)
        return JsonResponse({"status": "pending", "cache_key": cache_key})


def diagnostic_result(request):
    cache_key = request.GET.get("cache_key")
    result = cache.get(cache_key)
    print("Diagnostic result for cache key:", cache_key)
    if result:
        return JsonResponse({"status": "done", "response": result})
    print("No cached result found for key:", cache_key)
    return JsonResponse({"status": "pending"})


def formater_symptomes_en_texte(symptomes: dict) -> str:
    # Informations personnelles
    nom = symptomes["Identification"]["Nom complet"]
    age = symptomes["Identification"]["Âge"]
    date_naissance = symptomes["Identification"]["Date de naissance"]

    texte = f"Je m'appelle {nom}, j'ai {age} ans (né le {date_naissance}). Voici toutes mes informations médicales. J'ai besoin d'un diagnostic basé sur les détails suivants :\n\n"

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


@method_decorator(login_required, name='dispatch')
class ConversationView(View):
    """
    Gère la création, la récupération et la suppression d'une conversation.
    """

    def post(self, request):
        # Création d'une nouvelle conversation
        conversation = Conversation.objects.create(user=request.user)
        return JsonResponse({"success": True, "conversation_id": conversation.id})

    def get(self, request, conversation_id):
        # Récupération d'une conversation et de ses messages
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
            messages = MessageIA.objects.filter(
                conversation=conversation,
                role__in=['user', 'synthese']
            ).order_by('id')

            messages_data = [{
                "content": msg.content,
                "role": msg.role,
                "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M")
            } for msg in messages]

            return JsonResponse({"success": True, "messages": messages_data})
        except Conversation.DoesNotExist:
            return JsonResponse({"success": False, "error": "Conversation non trouvée"})

    def delete(self, request, conversation_id):
        # Suppression d'une conversation
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
            conversation.delete()
            return JsonResponse({"success": True})
        except Conversation.DoesNotExist:
            return JsonResponse({"success": False, "error": "Conversation non trouvée"})

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

class ChatHistoryView(LoginRequiredMixin, TemplateView):
    template_name = "chat/history.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # On récupère toutes les conversations de ce user
        conversations = Conversation.objects.filter(user=user).order_by('-id')

        # Pour chaque conversation, on récupère les messages utiles
        chat_items = []
        for conv in conversations:
            # On récupère que les messages 'user' et 'synthese' dans l'ordre d'envoi
            messages = (
                MessageIA.objects
                    .filter(conversation=conv, role__in=['user', 'synthese'])
                    .order_by('id')
            )
            if messages.exists():
                chat_items.append({
                    "conversation": conv,
                    "messages": messages
                })

        context['chat_items'] = chat_items
        return context