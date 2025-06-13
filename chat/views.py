import json
import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import TemplateView
from django.views.generic.edit import FormView, CreateView, View
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from .models import UserProfile, FicheConsultation
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.core.cache import cache
import hashlib
from .tasks import analyse_symptomes_task, analyse_consultation_task, analyse_fiche_consultation_task
from celery.result import AsyncResult
from django.db import transaction
from django.contrib import messages
from asgiref.sync import sync_to_async
from .llm_config import gpt4, claude, gemini, synthese_llm
from langchain.schema import HumanMessage
from concurrent.futures import ThreadPoolExecutor
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import Conversation, MessageIA
from django.views import View
from .forms import FicheConsultationForm

from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

def stream_synthese(synthese_llm, synthese_message):
    """Générateur qui yield les tokens au fur et à mesure via Langchain streaming."""
    for chunk in synthese_llm.stream([synthese_message]):
        # chaque chunk est un ChatMessage dans Langchain
        if hasattr(chunk, 'content'):
            yield chunk.content

@method_decorator(csrf_exempt, name='dispatch')
class AnalyseSymptomesView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'chat/medecin.html')

    def post(self, request):
        try:
            data = json.loads(request.body)
            message = data.get('message', '').strip()
            
            if not message:
                return JsonResponse({'error': 'Message vide'}, status=400)

            # Lancer la tâche Celery de manière asynchrone
            task = analyse_symptomes_task.delay(message, request.user.id)
            
            return JsonResponse({
                'task_id': task.id,
                'status': 'processing',
                'message': 'Analyse en cours...'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Données JSON invalides'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@login_required
def check_task_status(request, task_id):
    """
    Vérifier le statut d'une tâche Celery
    """
    try:
        task_result = AsyncResult(task_id)
        
        if task_result.state == 'PENDING':
            response = {
                'state': task_result.state,
                'status': 'En attente...'
            }
        elif task_result.state == 'PROGRESS':
            response = {
                'state': task_result.state,
                'current': task_result.info.get('current', 0),
                'total': task_result.info.get('total', 1),
                'status': task_result.info.get('status', '')
            }
        elif task_result.state == 'SUCCESS':
            response = {
                'state': task_result.state,
                'result': task_result.result,
                'status': 'Terminé'
            }
        else:  # FAILURE
            response = {
                'state': task_result.state,
                'error': str(task_result.info),
                'status': 'Erreur'
            }
        
        return JsonResponse(response)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def diagnostic_result(request):
    cache_key = request.GET.get("cache_key")
    if not cache_key:
        return JsonResponse({"status": "error", "message": "Cache key manquant"})
    
    result = cache.get(cache_key)
    print(f"Diagnostic result for cache key: {cache_key}")
    
    if result:
        print(f"Found cached result: {result[:100]}...")
        return JsonResponse({"status": "done", "response": result})
    
    print(f"No cached result found for key: {cache_key}")
    return JsonResponse({"status": "pending"})

def formater_symptomes_en_texte(symptomes):
    """
    Formate les symptômes en texte pour l'analyse LLM.
    Si c'est un dict structuré, utilise formater_formulaire_en_texte.
    Sinon, retourne le texte brut.
    """
    if isinstance(symptomes, dict):
        return formater_formulaire_en_texte(symptomes)
    return str(symptomes)

def formater_formulaire_en_texte(symptomes: dict) -> str:
    """Formate spécifiquement un formulaire de consultation en texte"""
    try:
        # Informations personnelles
        identification = symptomes.get("Identification", {})
        nom = identification.get("Nom complet", "Non spécifié")
        age = identification.get("Âge", "Non spécifié")
        date_naissance = identification.get("Date de naissance", "Non spécifiée")
        telephone = identification.get("Téléphone", "Non spécifié")

        texte = f"Patient : {nom}, âge : {age} ans (né le {date_naissance}), téléphone : {telephone}\n\n"

        # Motif et histoire
        motif = symptomes.get('Motif de consultation', 'Non spécifié')
        histoire = symptomes.get('Histoire de la maladie', 'Non spécifiée')
        
        texte += f"MOTIF DE CONSULTATION :\n{motif}\n\n"
        texte += f"HISTOIRE DE LA MALADIE :\n{histoire}\n\n"

        # Plaintes
        plaintes = symptomes.get("Plaintes", {})
        if plaintes:
            texte += "PLAINTES ET SYMPTÔMES :\n"
            for k, v in plaintes.items():
                if v and v != "Non spécifié":
                    texte += f"- {k} : {v}\n"
            texte += "\n"

        # Signes vitaux
        signes_vitaux = symptomes.get("Signes vitaux", {})
        if signes_vitaux:
            texte += "SIGNES VITAUX :\n"
            for k, v in signes_vitaux.items():
                if v and v != "Non spécifié":
                    texte += f"- {k} : {v}\n"
            texte += "\n"

        # Antécédents personnels
        antecedents_perso = symptomes.get("Antécédents personnels", {})
        if antecedents_perso:
            texte += "ANTÉCÉDENTS PERSONNELS :\n"
            for k, v in antecedents_perso.items():
                if v:
                    status = "Oui" if isinstance(v, bool) and v else str(v)
                    if status not in ["False", "Non", ""]:
                        texte += f"- {k} : {status}\n"
            texte += "\n"

        # Antécédents familiaux
        antecedents_fam = symptomes.get("Antécédents familiaux", {})
        if antecedents_fam:
            texte += "ANTÉCÉDENTS FAMILIAUX :\n"
            for k, v in antecedents_fam.items():
                if v:
                    status = "Oui" if isinstance(v, bool) and v else str(v)
                    if status not in ["False", "Non", ""]:
                        texte += f"- {k} : {status}\n"
            texte += "\n"

        # Mode de vie
        mode_vie = symptomes.get("Mode de vie", {})
        if mode_vie:
            texte += "MODE DE VIE :\n"
            for k, v in mode_vie.items():
                if v and v != "Non spécifié":
                    texte += f"- {k} : {v}\n"
            texte += "\n"

        # Examen clinique
        examen = symptomes.get("Examen clinique", {})
        if examen:
            texte += "EXAMEN CLINIQUE :\n"
            for k, v in examen.items():
                if v and v != "Non spécifié":
                    texte += f"- {k} : {v}\n"
            texte += "\n"

        # Évaluation psychosociale
        psychosocial = symptomes.get("Évaluation psychosociale", {})
        if psychosocial:
            texte += "ÉVALUATION PSYCHOSOCIALE :\n"
            for k, v in psychosocial.items():
                if v and v != "Non spécifié":
                    texte += f"- {k} : {v}\n"
            texte += "\n"

        texte += "\nVeuillez fournir un diagnostic médical complet basé sur ces informations."
        
        return texte
        
    except Exception as e:
        print(f"Erreur lors du formatage du formulaire : {e}")
        return f"Données patient : {json.dumps(symptomes, indent=2, ensure_ascii=False)}"


@login_required
@require_http_methods(["POST"])
def new_conversation(request):
    conversation = Conversation.objects.create(user=request.user)
    return JsonResponse({"success": True, "conversation_id": conversation.id})


@login_required
def get_conversation(request, conversation_id):
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


@login_required
@require_http_methods(["DELETE"])
def delete_conversation(request, conversation_id):
    try:
        conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        conversation.delete()
        return JsonResponse({"success": True})
    except Conversation.DoesNotExist:
        return JsonResponse({"success": False, "error": "Conversation non trouvée"})


class FicheConsultationCreateView(LoginRequiredMixin, CreateView):
    model = FicheConsultation
    form_class = FicheConsultationForm
    template_name = "chat/fiche_consultation_form.html"
    success_url = reverse_lazy("consultations_distance")

    def form_valid(self, form):
        fiche = form.save(commit=False)
        fiche.present = self.request.user.userprofile.role  # Assure-toi que UserProfile existe
        fiche.save()
        analyse_fiche_consultation_task.delay(fiche.id)
        messages.success(self.request, "Fiche soumise et analyse IA lancée.")
        return redirect(self.success_url)

class RelancerAnalyseMedecinView(LoginRequiredMixin, View):
    def post(self, request, fiche_id):
        fiche = get_object_or_404(FicheConsultation, id=fiche_id)
        analyse_fiche_consultation_task.delay(fiche.id)
        messages.success(request, "Analyse IA relancée pour cette fiche.")
        return redirect("consultations_distance")

# ...existing code...

class FicheConsultationCreateView(LoginRequiredMixin, CreateView):
    model = FicheConsultation
    form_class = FicheConsultationForm
    template_name = "chat/fiche_form.html"
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        print("Formulaire valide :", form.cleaned_data)
        fiche = form.save(commit=False)
        fiche.conversation = Conversation.objects.create(user=self.request.user)

        # Marquer comme consultation patient si c'est un patient
        if hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.role == 'patient':
            fiche.is_patient_distance = True
            fiche.status = 'en_analyse'

        fiche.save()

        # Construction du dictionnaire des symptômes
        symptomes = self.construire_dictionnaire_symptomes(fiche)

        def default_serializer(obj):
            if isinstance(obj, (datetime.date, datetime.datetime)):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} non sérialisable")

        # Traitement selon le rôle
        if hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.role == 'patient':
            # Pour un patient : traitement spécial avec redirection vers dashboard patient
            return self.traiter_consultation_patient_distance(fiche, symptomes, default_serializer)
        else:
            # Pour médecin/autres : traitement normal avec chat IA
            self.request.session["symptomes_diagnostic"] = json.dumps(symptomes, default=default_serializer)
            return redirect("analyse")

    def construire_dictionnaire_symptomes(self, fiche):
        """Construit le dictionnaire des symptômes à partir de la fiche"""
        return {
            "Identification": {
                "Nom complet": f"{fiche.nom} {fiche.postnom} {fiche.prenom}".strip(),
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
            "Motif de consultation": fiche.motif_consultation or "Non spécifié",
            "Histoire de la maladie": fiche.histoire_maladie or "Non spécifiée",
            "Plaintes": {
                "Céphalées": fiche.cephalees or "Non",
                "Vertiges": fiche.vertiges or "Non",
                "Palpitations": fiche.palpitations or "Non",
                "Troubles visuels": fiche.troubles_visuels or "Non",
                "Nycturie": fiche.nycturie or "Non",
            },
            "Signes vitaux": {
                "Température": f"{fiche.temperature}°C" if fiche.temperature else "Non mesurée",
                "SpO2": f"{fiche.spo2}%" if fiche.spo2 else "Non mesurée",
                "Tension artérielle": fiche.tension_arterielle or "Non mesurée",
                "Pouls": f"{fiche.pouls}/min" if fiche.pouls else "Non mesuré",
                "Fréquence respiratoire": f"{fiche.frequence_respiratoire}/min" if fiche.frequence_respiratoire else "Non mesurée",
                "Poids": f"{fiche.poids}kg" if fiche.poids else "Non mesuré",
            },
            "Antécédents personnels": {
                "Hypertension": fiche.hypertendu,
                "Diabète": fiche.diabetique,
                "Épilepsie": fiche.epileptique,
                "Troubles du comportement": fiche.trouble_comportement,
                "Gastrite": fiche.gastritique,
                "Autres antécédents": fiche.autres_antecedents or "Aucun",
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
                "Détail de l'activité physique": fiche.activite_physique_detail or "Non spécifié",
                "Alimentation habituelle": fiche.alimentation_habituelle or "Non spécifiée",
            },
            "Allergies": {
                "Allergie médicamenteuse": fiche.allergie_medicamenteuse,
                "Nom du médicament allergène": fiche.medicament_allergique or "Aucun",
            },
            "Traumatismes": {
                "Événement traumatique": fiche.evenement_traumatique,
                "Traumatisme lié au décès d'un enfant": fiche.trauma_deces_enfant,
                "État général": fiche.etat_general or "Non spécifié",
            },
            "Capacités": {
                "Capacité physique": fiche.capacite_physique,
                "Score physique": fiche.capacite_physique_score or "Non évalué",
                "Capacité psychologique": fiche.capacite_psychologique,
                "Score psychologique": fiche.capacite_psychologique_score or "Non évalué",
            },
            "Examen clinique": {
                "État général": fiche.etat,
                "Fièvre": fiche.febrile,
                "Coloration bulbaire": fiche.coloration_bulbaire,
                "Coloration palpébrale": fiche.coloration_palpebrale,
                "Téguments": fiche.tegument,
                "Tête": fiche.tete or "Normal",
                "Cou": fiche.cou or "Normal",
                "Paroi thoracique": fiche.paroi_thoracique or "Normale",
                "Poumons": fiche.poumons or "Normaux",
                "Cœur": fiche.coeur or "Normal",
                "Épigastre et hypochondres": fiche.epigastre_hypochondres or "Normal",
                "Péri-ombilical et flancs": fiche.peri_ombilical_flancs or "Normal",
                "Hypogastre et fosses iliaques": fiche.hypogastre_fosses_iliaques or "Normal",
                "Membres": fiche.membres or "Normaux",
                "Colonne et bassin": fiche.colonne_bassin or "Normal",
                "Examen gynécologique": fiche.examen_gynecologique or "Non réalisé",
            },
            "Évaluation psychosociale": {
                "Préoccupations": fiche.preoccupations or "Aucune",
                "Compréhension": fiche.comprehension or "Bonne",
                "Attentes": fiche.attentes or "Non spécifiées",
                "Engagement": fiche.engagement or "Bon",
            }
        }

    def traiter_consultation_patient_distance(self, fiche, symptomes, default_serializer):
        """Traite une consultation soumise par un patient à distance"""
        texte_symptomes = formater_symptomes_en_texte(symptomes)
        MessageIA.objects.create(
            conversation=fiche.conversation,
            role='user',
            content=texte_symptomes
        )

        def run_task():
            analyse_consultation_task.delay(fiche.id)
        transaction.on_commit(run_task)

        messages.success(
            self.request,
            'Votre consultation a été soumise avec succès! Elle est en cours d\'analyse par notre système IA. '
            'Un médecin vous contactera une fois l\'analyse terminée.'
        )
        return redirect('patient_dashboard')

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

class RegisterView(FormView):
    template_name = "chat/register.html"
    form_class = UserCreationForm
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        user = form.save()
        role = form.cleaned_data.get('role')
        # Vérifie si un UserProfile existe déjà pour cet utilisateur
        if not UserProfile.objects.filter(user=user).exists():
            UserProfile.objects.create(user=user, role=role)
        return super().form_valid(form)

class CustomLoginView(LoginView):
    template_name = "chat/login.html"
    authentication_form = AuthenticationForm

    def get_success_url(self):
        if hasattr(self.request.user, 'userprofile'):
            profile = self.request.user.userprofile
            if profile.role == 'medecin':
                return reverse_lazy('medecin_dashboard')
            elif profile.role == 'proche':
                return reverse_lazy('proche_dashboard')
            elif profile.role == 'patient':
                return reverse_lazy('patient_dashboard')
        return reverse_lazy('home')

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')

@login_required
def dashboard_redirect(request):
    if hasattr(request.user, 'userprofile'):
        profile = request.user.userprofile
        if profile.role == 'medecin':
            return redirect('medecin_dashboard')
        elif profile.role == 'proche':
            return redirect('proche_dashboard')
        elif profile.role == 'soignant':
            return redirect('soignant_dashboard')
        elif profile.role == 'patient':
            return redirect('patient_dashboard')
    return redirect('home')

@method_decorator(login_required, name='dispatch')
class MedecinDashboardView(TemplateView):
    template_name = "chat/medecin_dashboard.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer les consultations en attente de validation médecin
        consultations_en_attente = FicheConsultation.objects.filter(
            is_patient_distance=True,
            status='analyse_terminee'
        ).select_related('conversation__user').order_by('-created_at')
        
        context['consultations_en_attente'] = consultations_en_attente
        return context

@method_decorator(login_required, name='dispatch')
class ConsultationsDistanceView(TemplateView):
    template_name = "chat/consultations_distance.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        consultations_en_attente = FicheConsultation.objects.filter(
            is_patient_distance=True,
            status='analyse_terminee'
        ).order_by('-created_at')

        consultations_json = []
        for consultation in consultations_en_attente:
            consultations_json.append({
                'id': consultation.id,
                'nom': consultation.nom,
                'prenom': consultation.prenom,
                'age': consultation.age,
                'telephone': consultation.telephone,
                'motif_consultation': consultation.motif_consultation,
                'histoire_maladie': consultation.histoire_maladie,
                'temperature': consultation.temperature,
                'tension_arterielle': consultation.tension_arterielle,
                'pouls': consultation.pouls,
                'spo2': consultation.spo2,
                'cephalees': consultation.cephalees,
                'febrile': consultation.febrile,
                'status': consultation.status,
                'status_display': consultation.get_status_display(),
                'created_at': consultation.created_at.isoformat(),
                'diagnostic_ia': consultation.diagnostic_ia,  # <-- Ici on récupère la réponse IA de la base
            })
        context['consultations_en_attente'] = consultations_en_attente
        context['consultations_json'] = json.dumps(consultations_json)
        return context

# API pour les notifications en temps réel
@login_required
def api_consultations_distance(request):
    """API pour récupérer les consultations à distance via AJAX"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'medecin':
        return JsonResponse([], safe=False)
    
    consultations = FicheConsultation.objects.filter(
        is_patient_distance=True,
        status='analyse_terminee'
    ).select_related('conversation__user').order_by('-created_at')
    
    data = []
    for consultation in consultations:
        data.append({
            'id': consultation.id,
            'nom': consultation.nom,
            'prenom': consultation.prenom,
            'status': consultation.status,
            'created_at': consultation.created_at.isoformat(),
        })
    
    return JsonResponse(data, safe=False)

# ...existing code...

@login_required
def valider_diagnostic_medecin(request, fiche_id):
    """Permet au médecin de valider un diagnostic généré par l'IA"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'medecin':
        messages.error(request, "Accès non autorisé.")
        return redirect('home')
    
    try:
        fiche = FicheConsultation.objects.get(
            id=fiche_id, 
            is_patient_distance=True,
            status='analyse_terminee'
        )
        
        if request.method == 'POST':
            action = request.POST.get('action')
            commentaire_medecin = request.POST.get('commentaire', '')
            
            if action == 'valider':
                fiche.status = 'valide_medecin'
                fiche.commentaire_medecin = commentaire_medecin
                fiche.medecin_validateur = request.user
                fiche.date_validation = datetime.datetime.now()
                fiche.save()
                
                messages.success(request, "Diagnostic validé avec succès!")
                
            elif action == 'rejeter':
                fiche.status = 'rejete_medecin'
                fiche.commentaire_medecin = commentaire_medecin
                fiche.medecin_validateur = request.user
                fiche.save()
                
                messages.info(request, "Diagnostic rejeté. Le patient sera informé.")
            
            return redirect('medecin_dashboard')
            
        # GET : afficher les détails pour validation
        # Récupérer le diagnostic IA
        diagnostic_ia = None
        if fiche.conversation:
            diagnostic_message = MessageIA.objects.filter(
                conversation=fiche.conversation,
                role='synthese'
            ).last()
            if diagnostic_message:
                diagnostic_ia = diagnostic_message.content
        
        context = {
            'fiche': fiche,
            'diagnostic_ia': diagnostic_ia,
        }
        return render(request, 'chat/validation_diagnostic.html', context)
        
    except FicheConsultation.DoesNotExist:
        messages.error(request, "Consultation non trouvée.")
        return redirect('medecin_dashboard')

class PatientDashboardView(TemplateView):
    template_name = "chat/patient.html"

class MedecinDashboardView(TemplateView):
    template_name = "chat/medecin.html"

class ProcheDashboardView(TemplateView):
    template_name = "chat/proche_aidant.html"