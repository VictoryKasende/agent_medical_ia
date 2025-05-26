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



import hashlib
import json
import asyncio
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.core.cache import cache
from concurrent.futures import ThreadPoolExecutor
from .models import Conversation, MessageIA, FicheConsultation
from asgiref.sync import sync_to_async

from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.http import StreamingHttpResponse

from langchain.schema import HumanMessage
from .llm_config import gpt4, claude, gemini, synthese_llm

def stream_synthese(synthese_llm, synthese_message):
    """Générateur qui yield les tokens au fur et à mesure via Langchain streaming."""
    for chunk in synthese_llm.stream([synthese_message]):
        # chaque chunk est un ChatMessage dans Langchain
        if hasattr(chunk, 'content'):
            yield chunk.content

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
                conversation=conv, role__in=['user', 'synthese']
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
        symptomes = data.get("message")
        hash_key = hashlib.md5(symptomes.encode("utf-8")).hexdigest()
        cache_key = f"diagnostic_{hash_key}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse({"response": cached_result})

        message = HumanMessage(content=f"""
            Symptômes du patient : {symptomes}
            Veuillez préciser :
            1. Analyses nécessaires
            2. Diagnostic(s)
            3. Traitement(s) avec posologie
            4. Éducation thérapeutique
            5. Références scientifiques fiables
            6. Répondre ensuite comme assistant médical rigoureux et bienveillant.
        """)

        conversation = Conversation.objects.create(user=request.user)
        MessageIA.objects.create(conversation=conversation, role='user', content=symptomes)

        results = {}
        try:
            results["gpt4"] = gpt4.invoke([message]).content
        except Exception as e:
            results["gpt4"] = f"Erreur avec GPT-4 : {e}"

        try:
            results["claude"] = claude.invoke([message]).content
        except Exception as e:
            results["claude"] = f"Erreur avec Claude : {e}"

        try:
            results["gemini"] = gemini.invoke([message]).content
        except Exception as e:
            results["gemini"] = f"Erreur avec Gemini : {e}"

        for model, content in results.items():
            MessageIA.objects.create(conversation=conversation, role=model, content=content)

        synthese_message = HumanMessage(content=f"""
            Trois experts ont donné leur avis :
            - 🤖 GPT-4 : {results['gpt4']}
            - 🧠 Claude 3 : {results['claude']}
            - 🔬 Gemini Pro : {results['gemini']}
            Formule une **synthèse claire, rigoureuse et prudente**, avec des **emojis** pour la lisibilité. 🩺
            Si le patient pose des questions, réponds comme un assistant médical qualifié.
        """)

        def token_stream():
            full_response = ""
            for chunk in stream_synthese(synthese_llm, synthese_message):
                yield chunk
                full_response += chunk
            cache.set(cache_key, full_response, timeout=3600)
            MessageIA.objects.create(conversation=conversation, role='synthese', content=full_response)

        return StreamingHttpResponse(token_stream(), content_type='text/plain; charset=utf-8')


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