# app/tasks.py
from celery import shared_task
from .models import Conversation, MessageIA
from django.core.cache import cache

def stream_synthese(synthese_llm, synthese_message):
    """Générateur qui yield les tokens au fur et à mesure via Langchain streaming."""
    for chunk in synthese_llm.stream([synthese_message]):
        # chaque chunk est un ChatMessage dans Langchain
        if hasattr(chunk, 'content'):
            yield chunk.content

@shared_task
def analyse_symptomes_task(symptomes, user_id, conversation_id, cache_key):
    # Import à l'intérieur pour éviter des soucis de "AppRegistryNotReady"
    from .llm_config import gpt4, claude, gemini, synthese_llm
    from langchain.schema import HumanMessage

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

    results = {}
    try:
        results['gpt4'] = gpt4.invoke([message]).content
    except Exception as e:
        results['gpt4'] = f"Erreur gpt4 : {e}"

    try:
        results['claude'] = claude.invoke([message]).content
    except Exception as e:
        results['claude'] = f"Erreur claude : {e}"

    try:
        results['gemini'] = gemini.invoke([message]).content
    except Exception as e:
        results['gemini'] = f"Erreur gemini : {e}"

    from .models import Conversation, MessageIA
    from .streaming import stream_synthese
    from django.core.cache import cache

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
    return full_response
