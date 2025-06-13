# app/tasks.py
from celery import shared_task
from celery.exceptions import Ignore
from django.core.cache import cache
from .llm_config import gpt4, claude, gemini, synthese_llm
from langchain.schema import HumanMessage
import json
import logging
from .models import FicheConsultation, MessageIA
import uuid

logger = logging.getLogger(__name__)

def stream_synthese(synthese_llm, synthese_message):
    """Générateur qui yield les tokens au fur et à mesure via Langchain streaming."""
    for chunk in synthese_llm.stream([synthese_message]):
        if hasattr(chunk, 'content'):
            yield chunk.content

def call_llm(prompt):
    # Remplace par ton vrai appel LLM si besoin
    return "Réponse simulée du LLM pour : " + prompt

def execute_symptomes_analysis(symptomes_text, user_id=None):
    """
    Fonction Python pure pour analyser les symptômes (sans contexte Celery)
    """
    try:
        # Étape 1: Analyse avec GPT-4
        gpt4_response = gpt4.invoke([HumanMessage(content=symptomes_text)])
        if hasattr(gpt4_response, "content"):
            gpt4_result = gpt4_response.content
        else:
            gpt4_result = "".join([chunk.content for chunk in gpt4_response])

        # Étape 2: Analyse avec Claude
        claude_response = claude.invoke([HumanMessage(content=symptomes_text)])
        if hasattr(claude_response, "content"):
            claude_result = claude_response.content
        else:
            claude_result = "".join([chunk.content for chunk in claude_response])

        # Étape 3: Synthèse finale
        synthese_prompt = f"""
        Vous êtes un médecin expert. Analysez ces deux diagnostics et fournissez une synthèse médicale complète.

        Diagnostic GPT-4:
        {gpt4_result}

        Diagnostic Claude:
        {claude_result}

        Fournissez une synthèse qui inclut:
        1. Diagnostic le plus probable
        2. Diagnostics différentiels
        3. Examens complémentaires recommandés
        4. Traitement suggéré
        5. Conseils de prévention
        """

        # Utilisation du streaming : concatène les chunks pour obtenir la synthèse complète
        synthese_chunks = []
        for chunk in synthese_llm.stream([HumanMessage(content=synthese_prompt)]):
            if hasattr(chunk, "content"):
                synthese_chunks.append(chunk.content)
            else:
                synthese_chunks.append(str(chunk))
        synthese_result = "".join(synthese_chunks)

        return {
            'gpt4_analysis': gpt4_result,
            'claude_analysis': claude_result,
            'synthese': synthese_result,
            'status': 'completed'
        }

    except Exception as exc:
        logger.error(f"Erreur dans execute_symptomes_analysis: {str(exc)}")
        raise exc

@shared_task(bind=True)
def analyse_symptomes_task(self, symptomes_text, user_id=None):
    """
    Tâche Celery pour analyser les symptômes de manière asynchrone
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 3, 'status': "Démarrage de l'analyse..."}
        )

        # Étape 1: Analyse avec GPT-4
        self.update_state(
            state='PROGRESS',
            meta={'current': 1, 'total': 3, 'status': "Analyse avec GPT-4..."}
        )
        gpt4_response = gpt4.invoke([HumanMessage(content=symptomes_text)])
        if hasattr(gpt4_response, "content"):
            gpt4_result = gpt4_response.content
        else:
            # Si c'est un flux (stream), concatène les morceaux
            gpt4_result = "".join([chunk.content for chunk in gpt4_response])

        # Étape 2: Analyse avec Claude
        self.update_state(
            state='PROGRESS',
            meta={'current': 2, 'total': 3, 'status': "Analyse avec Claude..."}
        )
        claude_response = claude.invoke([HumanMessage(content=symptomes_text)])
        if hasattr(claude_response, "content"):
            claude_result = claude_response.content
        else:
            claude_result = "".join([chunk.content for chunk in claude_response])

        # Étape 3: Synthèse finale
        self.update_state(
            state='PROGRESS',
            meta={'current': 3, 'total': 3, 'status': "Synthèse finale..."}
        )
        synthese_prompt = f"""
        Vous êtes un médecin expert. Analysez ces deux diagnostics et fournissez une synthèse médicale complète.

        Diagnostic GPT-4:
        {gpt4_result}

        Diagnostic Claude:
        {claude_result}

        Fournissez une synthèse qui inclut:
        1. Diagnostic le plus probable
        2. Diagnostics différentiels
        3. Examens complémentaires recommandés
        4. Traitement suggéré
        5. Conseils de prévention
        """

        # Utilisation du streaming : concatène les chunks pour obtenir la synthèse complète
        synthese_chunks = []
        for chunk in synthese_llm.stream([HumanMessage(content=synthese_prompt)]):
            if hasattr(chunk, "content"):
                synthese_chunks.append(chunk.content)
            else:
                synthese_chunks.append(str(chunk))
        synthese_result = "".join(synthese_chunks)

        # Résultat final
        result = {
            'gpt4_analysis': gpt4_result,
            'claude_analysis': claude_result,
            'synthese': synthese_result,
            'status': 'completed'
        }

        # Stocker le résultat en cache pour 30 minutes
        try:
            import uuid

            if hasattr(self, "request") and hasattr(self.request, "id"):
                cache_key = f"analysis_result_{self.request.id}"
            else:
                cache_key = f"analysis_result_{uuid.uuid4()}"
            cache.set(cache_key, result, 1800)

        except Exception:
            logger.warning("Erreur lors de la mise en cache du résultat")

        return result

    except Exception as exc:
        logger.error(f"Erreur dans analyse_symptomes_task: {str(exc)}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(exc), 'status': "Erreur lors de l'analyse"}
        )
        raise Ignore()

@shared_task(bind=True)
def analyse_consultation_task(self, fiche_id):
    """
    Tâche Celery pour analyser une consultation médicale
    """
    try:
        fiche = FicheConsultation.objects.get(id=fiche_id)
        
        # Mise à jour du statut
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 2, 'status': 'Préparation de l\'analyse...'}
        )
        
        # Construire le dictionnaire des symptômes
        from .views import FicheConsultationCreateView
        view_instance = FicheConsultationCreateView()
        symptomes_dict = view_instance.construire_dictionnaire_symptomes(fiche)
        
        # Convertir en texte
        from .views import formater_formulaire_en_texte
        symptomes_text = formater_formulaire_en_texte(symptomes_dict)

        # Lancer l'analyse
        self.update_state(
            state='PROGRESS',
            meta={'current': 1, 'total': 2, 'status': 'Analyse en cours...'}
        )

        # Appel de la fonction Python pure
        analysis_result = execute_symptomes_analysis(symptomes_text, fiche.conversation.user.id if fiche.conversation else None)

        fiche.diagnostic_ia = analysis_result.get('synthese', '')
        fiche.status = 'analyse_terminee'
        fiche.save()
        
        if fiche.conversation:
            MessageIA.objects.create(
                conversation=fiche.conversation,
                role='synthese',
                content=fiche.diagnostic_ia
            )
        
        self.update_state(
            state='SUCCESS',
            meta={'current': 2, 'total': 2, 'status': 'Analyse terminée'}
        )
        
        return {
            'fiche_id': fiche_id,
            'status': 'completed',
            'analysis': analysis_result
        }
        
    except Exception as exc:
        logger.error(f"Erreur dans analyse_consultation_task: {str(exc)}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(exc), 'status': 'Erreur lors de l\'analyse'}
        )
        raise Ignore()

@shared_task
def analyse_fiche_consultation_task(fiche_id):
    fiche = FicheConsultation.objects.get(id=fiche_id)
    prompt = f"Nom: {fiche.nom if hasattr(fiche, 'nom') else fiche.id}, Symptômes: {fiche.motif_consultation}"
    try:
        result = call_llm(prompt)
        fiche.commentaire_medecin = result
        fiche.status = "analyse_terminee"
        fiche.save()
    except Exception:
        fiche.commentaire_medecin = "Une erreur est survenue. Veuillez réessayer."
        fiche.status = "en_analyse"
        fiche.save()

    # Création du message de synthèse dans la conversation
    MessageIA.objects.create(
        conversation=fiche.conversation,
        role='synthese',
        content=fiche.diagnostic_ia
    )

    analyse_consultation_task.delay(fiche.id)


