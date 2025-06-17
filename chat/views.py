import json
import datetime
import hashlib

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import TemplateView, View
from django.views.generic.edit import FormView, CreateView
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import login
from django.http import JsonResponse
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction

from .forms import FicheConsultationForm
from .models import Conversation, MessageIA, FicheConsultation
from .tasks import analyse_symptomes_task

def stream_synthese(synthese_llm, synthese_message):
    """Générateur qui yield les tokens au fur et à mesure via Langchain streaming."""
    for chunk in synthese_llm.stream([synthese_message]):
        if hasattr(chunk, 'content'):
            yield chunk.content

class RegisterView(FormView):
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
        return reverse_lazy('dashboard_redirect')

class CustomLogoutView(LogoutView):
    next_page = 'login'

class HomeView(LoginRequiredMixin, TemplateView):
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

        # Reprise ou création de conversation
        if conversation_id:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        else:
            conversation = Conversation.objects.create(user=request.user)

        # Enregistrement immédiat du message
        MessageIA.objects.create(
            conversation=conversation,
            role='user',
            content=message_text
        )

        # Clé de cache pour le résultat IA
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
    if result:
        return JsonResponse({"status": "done", "response": result})
    return JsonResponse({"status": "pending"})

def formater_symptomes_en_texte(symptomes: dict) -> str:
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
        conversation = Conversation.objects.create(user=request.user)
        return JsonResponse({"success": True, "conversation_id": conversation.id})

    def get(self, request, conversation_id):
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
        fiche = form.save(commit=False)
        fiche.conversation = Conversation.objects.create(user=self.request.user)
        fiche.save()

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
        conversations = Conversation.objects.filter(user=user).order_by('-id')
        chat_items = []
        for conv in conversations:
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

class RelancerAnalyseMedecinView(View):
    """
    Relance l'analyse IA pour une fiche de consultation donnée.
    """
    def post(self, request, fiche_id):
        fiche = get_object_or_404(FicheConsultation, id=fiche_id)
        # Ici, tu peux relancer la tâche Celery d'analyse IA si besoin
        # Par exemple :
        # from .tasks import analyse_fiche_consultation_task
        # analyse_fiche_consultation_task.delay(fiche.id)
        messages.success(request, "L'analyse IA a été relancée pour ce dossier.")
        return redirect(reverse_lazy('consultation'))

class PatientDashboardView(TemplateView):
    template_name = "chat/patient.html"

class MedecinDashboardView(TemplateView):
    template_name = "chat/home.html"  # ou le nom du template voulu

class ProcheDashboardView(TemplateView):
    template_name = "chat/dashboard_proche.html"

class ConsultationsDistanceView(TemplateView):
    template_name = "chat/consultations_distance.html"

def check_task_status(request, task_id):
    """
    Vue simple pour vérifier le statut d'une tâche Celery.
    """
    from celery.result import AsyncResult
    from agent_medical_ia.celery import app  # adapte ce chemin si besoin

    result = AsyncResult(task_id, app=app)
    response = {
        "task_id": task_id,
        "state": result.state,
        "result": result.result if result.state == "SUCCESS" else None,
        "info": str(result.info) if result.info else None,
    }
    return JsonResponse(response)

def api_consultations_distance(request):
    """
    API qui retourne la liste des fiches de consultation à distance (exemple : toutes les fiches).
    Adapte le filtre selon ton besoin.
    """
    fiches = FicheConsultation.objects.all().values(
        'id', 'nom', 'prenom', 'date_naissance', 'age', 'numero_dossier'
    )
    return JsonResponse(list(fiches), safe=False)

def valider_diagnostic_medecin(request, fiche_id):
    """
    Exemple de validation d'un diagnostic par le médecin.
    Tu peux adapter la logique selon ton besoin.
    """
    fiche = get_object_or_404(FicheConsultation, id=fiche_id)
    # Ici, tu peux ajouter la logique de validation (ex : fiche.validated = True)
    # fiche.validated = True
    # fiche.save()
    messages.success(request, "Diagnostic validé pour ce dossier.")
    return redirect('consultation')  # adapte la redirection selon ton projet

@login_required
def redirection_dashboard(request):
    if request.user.groups.filter(name='medecin').exists():
        consultations_en_attente = FicheConsultation.objects.filter(status='en_attente')
        # Ajout de l'historique des conversations pour le médecin
        conversations = Conversation.objects.filter(user=request.user).order_by('-created_at')
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
        return render(
            request,
            'chat/home.html',
            {
                'consultations_en_attente': consultations_en_attente,
                'chat_items': chat_items,
                'user': request.user
            }
        )
    else:
        consultations_patient = FicheConsultation.objects.all()
        consultations_patient = [
            c for c in consultations_patient
            if not (
                c.diagnostic_ia and
                c.diagnostic_ia.strip().startswith("Voici une synthèse médicale complète")
            )
        ]
        return render(request, 'chat/patient.html', {'consultations_patient': consultations_patient})