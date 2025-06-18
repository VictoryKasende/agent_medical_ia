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
        return reverse_lazy('dashboard_redirect')

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
        conversations = Conversation.objects.filter(
            user=user
        ).order_by('id')
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
    success_url = reverse_lazy('patient_dashboard')

    def form_valid(self, form):
        fiche = form.save(commit=False)
        fiche.conversation = Conversation.objects.create(user=self.request.user)
        fiche.status = 'en_attente'
        fiche.save()
        # Lance l'analyse IA en tâche de fond (asynchrone)
        analyse_symptomes_task.delay(fiche.id)
        messages.success(self.request, "Votre formulaire a été envoyé. Un médecin va l'analyser.")
        return super().form_valid(form)

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
        from .tasks import analyse_fiche_consultation_task
        analyse_fiche_consultation_task.delay(fiche.id)
        messages.success(request, "L'analyse IA a été relancée pour ce dossier.")
        return redirect(reverse_lazy('consultation'))

class PatientDashboardView(TemplateView):
    template_name = "chat/patient.html"

class MedecinDashboardView(TemplateView):
    template_name = "chat/home.html"  # ou le nom du template voulu

class ProcheDashboardView(TemplateView):
    template_name = "chat/dashboard_proche.html"

class ConsultationsDistanceView(LoginRequiredMixin, TemplateView):
    template_name = "chat/consultations_distance.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fiches = FicheConsultation.objects.all().order_by('-created_at')
        context['fiches'] = fiches
        context['consultations_json'] = json.dumps([
            {
                "id": f.id,
                "nom": f.nom,
                "prenom": f.prenom,
                "age": f.age,
                "created_at": f.created_at.isoformat(),
                "motif_consultation": f.motif_consultation,
                "cephalees": f.cephalees,
                "febrile": f.febrile,
                "status": f.status,
                "status_display": f.get_status_display(),
                "telephone": f.telephone,
                "temperature": f.temperature,
                "tension_arterielle": f.tension_arterielle,
                "pouls": f.pouls,
                "spo2": f.spo2,
                "histoire_maladie": f.histoire_maladie,
                "diagnostic_ia": f.diagnostic_ia,  # <-- pour affichage IA
            }
            for f in fiches
        ])
        return context

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
    fiches = FicheConsultation.objects.filter(status='en_attente').values(
        'id', 'nom', 'prenom', 'date_naissance', 'age', 'numero_dossier', 'created_at', 'status'
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