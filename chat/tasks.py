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
            1. Analyses nécessaires
            2. Diagnostic(s)
            3. Traitement(s) avec posologie
            4. Éducation thérapeutique
            5. Références scientifiques fiables
            6. Répondre ensuite comme assistant médical rigoureux et bienveillant.
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
        return full_response

    except Exception as exc:
        self.update_state(
            state='FAILURE',
            meta={'error': str(exc), 'status': "Erreur lors de l'analyse"}
        )
        raise Ignore()

# --- Fonctions avancées pour analyse de fiches et consultation ---

@shared_task(bind=True)
def analyse_fiche_consultation_task(self, fiche_id):
    """
    Analyse une fiche de consultation complète et stocke le diagnostic IA dans la fiche.
    """
    try:
        from .llm_config import gpt4
        from langchain.schema import HumanMessage

        fiche = FicheConsultation.objects.get(id=fiche_id)
        prompt = f"""
        Patient : {fiche.nom}, {fiche.age} ans
        Symptômes : {fiche.motif_consultation} - {fiche.histoire_maladie}
        Signes vitaux : Température {fiche.temperature}, SpO2 {fiche.spo2}, TA {fiche.tension_arterielle}, Pouls {fiche.pouls}
        Antécédents : {fiche.autres_antecedents}
        Plaintes : Céphalées={fiche.cephalees}, Vertiges={fiche.vertiges}, Palpitations={fiche.palpitations}
        Examen clinique : {fiche.etat}
        Donne un diagnostic différentiel, examens complémentaires, traitement, conseils.
        """
        message = HumanMessage(content=prompt)
        result = gpt4.invoke([message]).content
        fiche.diagnostic_ia = result
        fiche.save()
        return result
    except Exception as exc:
        self.update_state(
            state='FAILURE',
            meta={'error': str(exc), 'status': "Erreur analyse fiche"}
        )
        raise Ignore()

@shared_task(bind=True)
def analyse_consultation_task(self, consultation_id):
    """
    Analyse une consultation médicale (exemple pour extension future).
    """
    try:
        from .llm_config import gpt4
        from langchain.schema import HumanMessage

        consultation = FicheConsultation.objects.get(id=consultation_id)
        prompt = f"""
        Consultation du patient {consultation.nom}, {consultation.age} ans.
        Motif : {consultation.motif_consultation}
        Histoire : {consultation.histoire_maladie}
        Examen : {consultation.etat}
        Propose un diagnostic, examens, traitement, conseils.
        """
        message = HumanMessage(content=prompt)
        result = gpt4.invoke([message]).content
        consultation.diagnostic_ia = result
        consultation.save()
        return result
    except Exception as exc:
        self.update_state(
            state='FAILURE',
            meta={'error': str(exc), 'status': "Erreur analyse consultation"}
        )
        raise Ignore()

def execute_symptomes_analysis(symptomes):
    """
    Fonction Python pure pour analyse rapide (hors Celery).
    """
    from .llm_config import gpt4
    from langchain.schema import HumanMessage
    message = HumanMessage(content=f"Analyse ces symptômes : {symptomes}")

@shared_task
def analyse_symptomes_task(fiche_id):
    fiche = FicheConsultation.objects.get(id=fiche_id)
    # Appel à ton LLM ici (OpenAI, local, etc.)
    # Par exemple :
    diagnostic_ia = appel_llm(fiche)  # fonction qui retourne le texte IA
    fiche.diagnostic_ia = diagnostic_ia
    fiche.status = 'analyse_terminee'
    fiche.save()


