# app/tasks.py
from celery import shared_task
from celery.exceptions import Ignore
from django.core.cache import cache
from .models import Conversation, MessageIA, FicheConsultation

def stream_synthese(synthese_llm, synthese_message):
    """Générateur qui yield les tokens au fur et à mesure via Langchain streaming."""
    for chunk in synthese_llm.stream([synthese_message]):
        if hasattr(chunk, 'content'):
            yield chunk.content

@shared_task(bind=True)
def analyse_symptomes_task(self, symptomes, user_id, conversation_id, cache_key):
    """
    Analyse les symptômes via plusieurs LLM en parallèle, stocke chaque réponse et la synthèse.
    Résultat final mis en cache.
    """
    try:
        from .llm_config import gpt4, claude, gemini, synthese_llm
        from langchain.schema import HumanMessage
        from concurrent.futures import ThreadPoolExecutor

        message = HumanMessage(content=f"""
            Symptômes du patient : {symptomes}
            Veuillez préciser :
            1. Decryptage du dossier médical et conduite a tenir
            2. Analyses nécessaires
            3. Diagnostic(s) et argumentation et justification des avis avec référence
            4. Traitement(s) avec posologie
            5. Éducation thérapeutique
            6. Références scientifiques fiables en style APA
            7. Répondre ensuite comme assistant médical rigoureux et bienveillant.
        """)

        def gpt4_call():
            return gpt4.invoke([message]).content

        def claude_call():
            return claude.invoke([message]).content

        def gemini_call():
            return gemini.invoke([message]).content

        with ThreadPoolExecutor(max_workers=3) as executor:
            tasks = {
                'gpt4': executor.submit(gpt4_call),
                'claude': executor.submit(claude_call),
                'gemini': executor.submit(gemini_call),
            }
            results = {}
            for name, future in tasks.items():
                try:
                    results[name] = future.result(timeout=120)
                except Exception as e:
                    results[name] = f"Erreur {name} : {e}"

        conv = Conversation.objects.get(id=conversation_id)
        for model, content in results.items():
            MessageIA.objects.create(conversation=conv, role=model, content=content)

        synthese_message = HumanMessage(content=f"""
            Trois experts ont donné leur avis :
            - 🤖 GPT-4 : {results['gpt4']}
            - 🧠 Claude 3 : {results['claude']}
            - 🔬 Gemini Pro : {results['gemini']}
            Formule une **synthèse claire, rigoureuse et prudente**, avec des **emojis** pour la lisibilité. 🩺
            Si le patient pose des questions, réponds comme un assistant médical qualifié.
        """)
        full_response = ""
        for chunk in stream_synthese(synthese_llm, synthese_message):
            full_response += chunk
        MessageIA.objects.create(conversation=conv, role='synthese', content=full_response)
        cache.set(cache_key, full_response, timeout=3600)

        try:
            if conv.fiche:
                conv.fiche.diagnostic_ia = full_response
                conv.fiche.status = 'analyse_terminee'
                conv.fiche.save()
        except FicheConsultation.DoesNotExist:
                pass
        return full_response

    except Exception as exc:
        self.update_state(
            state='FAILURE',
            meta={'error': str(exc), 'status': "Erreur lors de l'analyse"}
        )
        raise Ignore()