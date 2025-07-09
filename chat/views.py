import json
import hashlib
import base64

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from django.views.generic.edit import CreateView
from django.views.generic import DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.http import JsonResponse
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
from django.contrib.auth.decorators import user_passes_test
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from django.http import Http404

from .forms import FicheConsultationForm
from .models import Conversation, MessageIA, FicheConsultation
from .tasks import analyse_symptomes_task

PATIENT = 'patient'
MEDECIN = 'medecin'

def is_patient(user):
    """Vérifie si l'utilisateur est un patient."""
    return user.is_authenticated and user.role == PATIENT

def is_medecin(user):
    """Vérifie si l'utilisateur est un médecin."""
    return user.is_authenticated and user.role == MEDECIN

def stream_synthese(synthese_llm, synthese_message):
    """Générateur qui yield les tokens au fur et à mesure via Langchain streaming."""
    for chunk in synthese_llm.stream([synthese_message]):
        if hasattr(chunk, 'content'):
            yield chunk.content

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(user_passes_test(is_medecin), name='dispatch')
class AnalyseSymptomesView(LoginRequiredMixin, View):

    template_name = "chat/home.html"

    def get(self, request):

        conversations = Conversation.objects.all().order_by('-created_at')
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

@login_required
def chat_history_partial(request):
    conversations = Conversation.objects.all().order_by('-created_at')
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
    html = render_to_string("chat/chat_history.html", {"chat_items": chat_items})
    return JsonResponse({"html": html})

def diagnostic_result(request):
    cache_key = request.GET.get("cache_key")
    result = cache.get(cache_key)
    if result:
        return JsonResponse({"status": "done", "response": result})
    return JsonResponse({"status": "pending"})

@method_decorator(user_passes_test(is_medecin), name='dispatch')
class ConversationView(LoginRequiredMixin, View):
    """
    Gère la création, la récupération, modification et la suppression d'une conversation.
    """

    def post(self, request):
        conversation = Conversation.objects.create(user=request.user)
        return JsonResponse({"success": True, "conversation_id": conversation.id})

    def get(self, request, conversation_id):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
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
        

    def put(self, request, conversation_id):
        data = json.loads(request.body)
        new_name = data.get("nom", "")
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
            conversation.nom = new_name
            conversation.save()
            return JsonResponse({"success": True, "nom": conversation.nom})
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
        fiche.status = 'en_analyse'
        fiche.is_patient_distance = True if is_patient(self.request.user) else False
        fiche.medecin_validateur = self.request.user if is_medecin(self.request.user) else None
        fiche.save()

        # Formatage des données en texte pour l'IA
        texte = self.formater_fiche_en_texte(fiche)

        print("Texte formaté pour l'IA :", texte)

        # Lancer la tâche d'analyse
        user_id = self.request.user.id
        conversation_id = fiche.conversation.id

        MessageIA.objects.create(
            conversation=fiche.conversation,
            role='user',
            content=texte
        )

        hash_key = hashlib.md5(texte.encode("utf-8")).hexdigest()
        cache_key = f"diagnostic_{hash_key}"

        def run_task():
            analyse_symptomes_task.delay(texte, user_id, conversation_id, cache_key)

        transaction.on_commit(run_task)

        messages.success(self.request, "Votre formulaire a été envoyé. Un médecin va l'analyser.")
        return super().form_valid(form)

    def formater_fiche_en_texte(self, fiche):
        texte = f"Je suis docteur {fiche.medecin_validateur.username if fiche.medecin_validateur else ''}, j'ai un patient tel que décrit ci-dessous.\n"
        texte += f"Je m'appelle {fiche.nom} {fiche.postnom} {fiche.prenom}, j'ai {fiche.age} ans (né le {fiche.date_naissance}), mon numéro de téléphone est {fiche.telephone}. "
        texte += f"Je suis {fiche.etat_civil.lower()}, j'exerce comme {fiche.occupation}. "
        texte += f"J'habite sur l'avenue {fiche.avenue}, quartier {fiche.quartier}, commune {fiche.commune}.\n\n"

        texte += "Personne à contacter en cas d'urgence : "
        texte += f"{fiche.contact_nom}, téléphone : {fiche.contact_telephone}, adresse : {fiche.contact_adresse}.\n\n"

        texte += f"Date de consultation : {fiche.date_consultation} à {fiche.heure_debut}.\n\n"

        texte += f"Motif de consultation : {fiche.motif_consultation or 'Non renseigné'}\n"
        texte += f"Histoire de la maladie : {fiche.histoire_maladie or 'Non renseigné'}\n\n"

        texte += "Plaintes :\n"
        texte += f"- Céphalées : {'Oui' if fiche.cephalees else 'Non'}\n"
        texte += f"- Vertiges : {'Oui' if fiche.vertiges else 'Non'}\n"
        texte += f"- Palpitations : {'Oui' if fiche.palpitations else 'Non'}\n"
        texte += f"- Troubles visuels : {'Oui' if fiche.troubles_visuels else 'Non'}\n"
        texte += f"- Nycturie : {'Oui' if fiche.nycturie else 'Non'}\n"

        texte += "\nSignes vitaux :\n"
        texte += f"- Température : {fiche.temperature or 'Non renseigné'} °C\n"
        texte += f"- SpO2 : {fiche.spo2 or 'Non renseigné'} %\n"
        texte += f"- Tension artérielle : {fiche.tension_arterielle or 'Non renseigné'}\n"
        texte += f"- Pouls : {fiche.pouls or 'Non renseigné'} bpm\n"
        texte += f"- Fréquence respiratoire : {fiche.frequence_respiratoire or 'Non renseignée'}\n"
        texte += f"- Poids : {fiche.poids or 'Non renseigné'} kg\n"

        texte += "\nAntécédents personnels :\n"
        texte += f"- Hypertension : {'Oui' if fiche.hypertendu else 'Non'}\n"
        texte += f"- Diabète : {'Oui' if fiche.diabetique else 'Non'}\n"
        texte += f"- Épilepsie : {'Oui' if fiche.epileptique else 'Non'}\n"
        texte += f"- Troubles du comportement : {'Oui' if fiche.trouble_comportement else 'Non'}\n"
        texte += f"- Gastrite : {'Oui' if fiche.gastritique else 'Non'}\n"
        texte += f"- Autres antécédents : {fiche.autres_antecedents or 'Aucun'}\n"

        texte += "\nAntécédents familiaux :\n"
        texte += f"- Drépanocytose : {'Oui' if fiche.familial_drepanocytaire else 'Non'}\n"
        texte += f"- Diabète : {'Oui' if fiche.familial_diabetique else 'Non'}\n"
        texte += f"- Obésité : {'Oui' if fiche.familial_obese else 'Non'}\n"
        texte += f"- Hypertension : {'Oui' if fiche.familial_hypertendu else 'Non'}\n"
        texte += f"- Troubles du comportement : {'Oui' if fiche.familial_trouble_comportement else 'Non'}\n"
        texte += f"- Lien avec la mère : {'Oui' if fiche.lien_mere else 'Non'}\n"
        texte += f"- Lien avec le père : {'Oui' if fiche.lien_pere else 'Non'}\n"
        texte += f"- Lien avec le frère : {'Oui' if fiche.lien_frere else 'Non'}\n"
        texte += f"- Lien avec la sœur : {'Oui' if fiche.lien_soeur else 'Non'}\n"

        texte += "\nMode de vie :\n"
        texte += f"- Tabac : {fiche.tabac}\n"
        texte += f"- Alcool : {fiche.alcool}\n"
        texte += f"- Activité physique : {fiche.activite_physique}\n"
        texte += f"- Détail de l'activité physique : {fiche.activite_physique_detail or 'Non précisé'}\n"
        texte += f"- Alimentation habituelle : {fiche.alimentation_habituelle or 'Non précisée'}\n"

        texte += "\nAllergies :\n"
        texte += f"- Allergie médicamenteuse : {'Oui' if fiche.allergie_medicamenteuse else 'Non'}\n"
        texte += f"- Médicament allergène : {fiche.medicament_allergique or 'Aucun'}\n"

        texte += "\nTraumatismes :\n"
        texte += f"- Événement traumatique : {fiche.evenement_traumatique}\n"
        texte += f"- Divorce : {'Oui' if fiche.trauma_divorce else 'Non'}\n"
        texte += f"- Perte de parent : {'Oui' if fiche.trauma_perte_parent else 'Non'}\n"
        texte += f"- Décès d'époux(se) : {'Oui' if fiche.trauma_deces_epoux else 'Non'}\n"
        texte += f"- Décès d’enfant : {'Oui' if fiche.trauma_deces_enfant else 'Non'}\n"
        texte += f"- État général : {fiche.etat_general or 'Non renseigné'}\n"

        texte += "\nCapacités :\n"
        texte += f"- Capacité physique : {fiche.capacite_physique}\n"
        texte += f"- Score physique : {fiche.capacite_physique_score or 'Non renseigné'}\n"
        texte += f"- Capacité psychologique : {fiche.capacite_psychologique}\n"
        texte += f"- Score psychologique : {fiche.capacite_psychologique_score or 'Non renseigné'}\n"

        texte += "\nExamen clinique :\n"
        texte += f"- État : {fiche.etat}\n"
        texte += f"- Fièvre : {fiche.febrile}\n"
        texte += f"- Coloration bulbaire : {fiche.coloration_bulbaire}\n"
        texte += f"- Coloration palpébrale : {fiche.coloration_palpebrale}\n"
        texte += f"- Téguments : {fiche.tegument}\n"
        texte += f"- Tête : {fiche.tete or 'RAS'}\n"
        texte += f"- Cou : {fiche.cou or 'RAS'}\n"
        texte += f"- Paroi thoracique : {fiche.paroi_thoracique or 'RAS'}\n"
        texte += f"- Poumons : {fiche.poumons or 'RAS'}\n"
        texte += f"- Cœur : {fiche.coeur or 'RAS'}\n"
        texte += f"- Épigastre et hypochondres : {fiche.epigastre_hypochondres or 'RAS'}\n"
        texte += f"- Péri-ombilical et flancs : {fiche.peri_ombilical_flancs or 'RAS'}\n"
        texte += f"- Hypogastre et fosses iliaques : {fiche.hypogastre_fosses_iliaques or 'RAS'}\n"
        texte += f"- Membres : {fiche.membres or 'RAS'}\n"
        texte += f"- Colonne et bassin : {fiche.colonne_bassin or 'RAS'}\n"
        texte += f"- Examen gynécologique : {fiche.examen_gynecologique or 'Non réalisé'}\n"

        texte += "\nÉvaluation psychosociale :\n"
        texte += f"- Préoccupations : {fiche.preoccupations or 'Non renseignées'}\n"
        texte += f"- Compréhension : {fiche.comprehension or 'Non renseignée'}\n"
        texte += f"- Attentes : {fiche.attentes or 'Non renseignées'}\n"
        texte += f"- Engagement : {fiche.engagement or 'Non renseigné'}\n"

        return texte

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

@method_decorator(user_passes_test(is_patient), name='dispatch')
class PatientDashboardView(TemplateView):
    template_name = "chat/patient.html"

@method_decorator(user_passes_test(is_medecin), name='dispatch')
class MedecinDashboardView(TemplateView):
    template_name = "chat/home.html" 
    

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
    fiches = FicheConsultation.objects.filter(status__in=['en_analyse', 'analyse_terminee']).values(
        'id', 'nom', 'prenom', 'date_naissance', 'age', 'numero_dossier', 'created_at', 'status'
    )
    data = []
    for f in fiches:
        f['status_display'] = FicheConsultation.STATUS_CHOICES_DICT.get(f['status'], f['status'])
        data.append(f)
    return JsonResponse(data, safe=False)

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
    
### ===========================================================
# Consultation presente des patients
@method_decorator(user_passes_test(is_medecin), name='dispatch')
class ConsultationPatientView(LoginRequiredMixin, TemplateView):
    template_name = 'chat/consultation_present.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        consultations_en_analyse = FicheConsultation.objects.filter(
            is_patient_distance=False,
            status='en_analyse'
        ).order_by('-id')

        consultations_terminees = FicheConsultation.objects.filter(
            is_patient_distance=False,
            status='analyse_terminee'
        ).order_by('-id')

        context['consultations_en_attente'] = consultations_en_analyse
        context['consultations_terminees'] = consultations_terminees
        context['consultations_en_attente_count'] = consultations_en_analyse.count()
        context['consultations_terminees_count'] = consultations_terminees.count()
        return context
    
class FicheConsultationUpdateView(LoginRequiredMixin, View):
    """
    Vue pour mettre à jour une fiche de consultation.
    """

    def get(self, request, fiche_id):
        fiche = get_object_or_404(FicheConsultation, id=fiche_id)
        form = FicheConsultationForm(instance=fiche)

        return render(request, 'chat/fiche_update.html', {'form': form, 'fiche': fiche})
    
    def post(self, request, fiche_id):
        fiche = get_object_or_404(FicheConsultation, id=fiche_id)
        form = FicheConsultationForm(request.POST, instance=fiche)

        if form.is_valid():
            fiche = form.save(commit=False)
            fiche.diagnostic = request.POST.get('diagnostic', '')
            fiche.traitement = request.POST.get('traitement', '')
            fiche.examen_complementaire = request.POST.get('examen_complementaire', '')
            fiche.recommandations = request.POST.get('recommandations', '')
            fiche.medecin_validateur = request.user 
            fiche.status = 'analyse_terminee'
            signature_data = request.POST.get('signature_data')
            print(f"Signature data reçue : {signature_data}")
            if signature_data:
                format, imgstr = signature_data.split(';base64,')
                ext = format.split('/')[-1]
                fiche.signature_medecin.save(
                    f'signature_{fiche.id}.{ext}',
                    ContentFile(base64.b64decode(imgstr)),
                    save=False
                )
            fiche.save()
            messages.success(request, "Fiche de consultation mise à jour avec succès.")
            
            if fiche.is_patient_distance:
                return redirect('consultation_patient_distant')
            return redirect('consultation_patient_present')
        else:
            messages.error(request, "Erreur lors de la mise à jour de la fiche.")
            return render(request, 'chat/fiche_update.html', {'form': form, 'fiche': fiche})
        
class UpdateFicheStatusView(LoginRequiredMixin, View):
    """
    Vue pour mettre à jour le statut d'une fiche de consultation.
    """

    def post(self, request, fiche_id):
        fiche = get_object_or_404(FicheConsultation, id=fiche_id)
        new_status = request.POST.get('status', 'en_attente')
        fiche.status = new_status
        fiche.save()
        messages.success(request, f"Statut de la fiche mis à jour : {fiche.get_status_display()}")
        
        if fiche.is_patient_distance:
            return redirect('consultation_patient_distant')
        else:
            return redirect('consultation_patient_present')

class FicheConsultationDetailView(LoginRequiredMixin, View):
    """
    Vue pour afficher les détails d'une fiche de consultation.
    """
    
    def get(self, request, fiche_id):
        fiche = get_object_or_404(FicheConsultation, id=fiche_id)
        context = {
            'consultation': fiche,
        }
        return render(request, 'chat/fiche_detail.html', context)
    
class PrintConsultationView(DetailView):
    model = FicheConsultation
    template_name = 'chat/consultation_print.html'  
    context_object_name = 'consultation'


### ===========================================================
# Consultation patient distant
@method_decorator(user_passes_test(is_medecin), name='dispatch')
class ConsultationPatientDistantView(LoginRequiredMixin, TemplateView):
    template_name = 'chat/consultation_patient_distant.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        consultations_en_analyse = FicheConsultation.objects.filter(
            is_patient_distance=True,
            status='en_analyse'
        ).order_by('-id')

        consultations_terminees = FicheConsultation.objects.filter(
            is_patient_distance=True,
            status='analyse_terminee'
        ).order_by('-id')

        context['consultations_en_attente'] = consultations_en_analyse
        context['consultations_terminees'] = consultations_terminees
        context['consultations_en_attente_count'] = consultations_en_analyse.count()
        context['consultations_terminees_count'] = consultations_terminees.count()
        return context
    
        
