# app/tasks.py
from celery import shared_task
from celery.exceptions import Ignore
from django.core.cache import cache

from .models import Conversation, FicheConsultation, MessageIA


def stream_synthese(synthese_llm, synthese_message):
    """Générateur qui yield les tokens au fur et à mesure via Langchain streaming."""
    for chunk in synthese_llm.stream([synthese_message]):
        if hasattr(chunk, "content"):
            yield chunk.content


@shared_task(bind=True)
def analyse_symptomes_task(self, symptomes, user_id, conversation_id, cache_key):
    """
    Analyse les symptômes via plusieurs LLM en parallèle, stocke chaque réponse et la synthèse.
    Résultat final mis en cache avec structure améliorée.
    """
    try:
        from concurrent.futures import ThreadPoolExecutor

        from langchain.schema import HumanMessage

        from .llm_config import claude, gemini, gpt4, synthese_llm

        # Prompt amélioré et structuré
        prompt_structure = f"""
        En tant qu'assistant médical IA, analysez les données suivantes et fournissez une réponse structurée :

        ## DONNÉES PATIENT
        {symptomes}

        ## FORMAT DE RÉPONSE REQUIS
        Veuillez structurer votre réponse selon les sections suivantes :

        ### 1. SYNTHÈSE CLINIQUE
        - Résumé des éléments cliniques clés
        - Points saillants du dossier

        ### 2. DIAGNOSTICS DIFFÉRENTIELS
        - Diagnostic principal avec niveau de certitude (%)
        - Diagnostics différentiels possibles
        - Argumentation clinique pour chaque hypothèse

        ### 3. ANALYSES PARACLINIQUES RECOMMANDÉES
        - Examens biologiques nécessaires
        - Imagerie médicale si indiquée
        - Autres explorations spécialisées
        - Priorisation selon l'urgence

        ### 4. TRAITEMENT PROPOSÉ
        - Traitement médicamenteux avec posologie précise
        - Durée du traitement
        - Surveillance nécessaire
        - Effets secondaires à surveiller

        ### 5. ÉDUCATION THÉRAPEUTIQUE ET CONSEILS
        - Conseils hygiéno-diététiques
        - Modifications du mode de vie
        - Signes d'alerte à surveiller
        - Suivi recommandé

        ### 6. RÉFÉRENCES BIBLIOGRAPHIQUES
        - Sources scientifiques pertinentes (PubMed, CINAHL, HAS)
        - Guidelines et recommandations officielles
        - Format : Auteur(s). Titre. Journal. Année. [URL si disponible]

        Soyez précis, prudent et toujours rappeler que cette analyse nécessite validation par un médecin.
        """

        message = HumanMessage(content=prompt_structure)

        def gpt4_call():
            return gpt4.invoke([message]).content

        def claude_call():
            return claude.invoke([message]).content

        def gemini_call():
            return gemini.invoke([message]).content

        with ThreadPoolExecutor(max_workers=3) as executor:
            tasks = {
                "gpt4": executor.submit(gpt4_call),
                "claude": executor.submit(claude_call),
                "gemini": executor.submit(gemini_call),
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

        # Prompt de synthèse amélioré
        synthese_message = HumanMessage(
            content=f"""
        Vous disposez des analyses de trois experts IA médicaux. Votre rôle est de produire une synthèse médicale 
        structurée et consensuelle.

        ## ANALYSES EXPERTES :

        ### 🤖 GPT-4 - Analyse Générale
        {results['gpt4']}

        ### 🧠 Claude 3 - Raisonnement Médical  
        {results['claude']}

        ### 🔬 Gemini Pro - Synthèse Diagnostique
        {results['gemini']}

        ## SYNTHÈSE DEMANDÉE :
        
        Produisez une synthèse médicale structurée en conservant le format à 6 sections :
        1. Synthèse clinique consensuelle
        2. Diagnostics avec niveaux de certitude
        3. Analyses paracliniques prioritaires
        4. Traitement avec posologies précises
        5. Éducation thérapeutique adaptée
        6. Références bibliographiques fiables

        ### DIRECTIVES :
        - Intégrez les points de convergence entre les experts
        - Signaler les divergences s'il y en a
        - Privilégiez la prudence et la sécurité du patient
        - Utilisez des emojis pour améliorer la lisibilité 🩺
        - Rappeler que cette analyse doit être validée par un médecin

        Répondez comme un assistant médical expert, rigoureux et bienveillant.
        """
        )

        full_response = ""
        for chunk in stream_synthese(synthese_llm, synthese_message):
            full_response += chunk
        MessageIA.objects.create(conversation=conv, role="synthese", content=full_response)
        cache.set(cache_key, full_response, timeout=3600)

        try:
            if conv.fiche:
                conv.fiche.diagnostic_ia = full_response
                conv.fiche.status = "analyse_terminee"
                conv.fiche.save()
        except FicheConsultation.DoesNotExist:
            pass
        return full_response

    except Exception as exc:
        self.update_state(state="FAILURE", meta={"error": str(exc), "status": "Erreur lors de l'analyse"})
        raise Ignore()


@shared_task(bind=True)
def process_data_export(self, export_job_id):
    """Traite un job d'export de données en arrière-plan."""
    try:
        import os
        from datetime import datetime

        import pandas as pd
        from django.conf import settings

        from .models import DataExportJob, FicheConsultation

        # Récupérer le job
        export_job = DataExportJob.objects.get(id=export_job_id)
        export_job.status = DataExportJob.ExportStatus.RUNNING
        export_job.started_at = timezone.now()
        export_job.save()

        # Construire la requête
        fiches_qs = FicheConsultation.objects.filter(
            date_consultation__range=[export_job.date_start, export_job.date_end]
        )

        # Appliquer les filtres
        filters = export_job.filters
        if filters.get("status"):
            fiches_qs = fiches_qs.filter(status__in=filters["status"])
        if filters.get("age_min"):
            fiches_qs = fiches_qs.filter(age__gte=filters["age_min"])
        if filters.get("age_max"):
            fiches_qs = fiches_qs.filter(age__lte=filters["age_max"])
        if filters.get("sexe"):
            fiches_qs = fiches_qs.filter(sexe=filters["sexe"])

        # Préparer les données
        data = []
        for fiche in fiches_qs:
            row = {
                "id": fiche.id,
                "numero_dossier": fiche.numero_dossier,
                "date_consultation": fiche.date_consultation,
                "age": fiche.age,
                "sexe": fiche.sexe,
                "status": fiche.status,
                "motif_consultation": fiche.motif_consultation,
                "hypertendu": fiche.hypertendu,
                "diabetique": fiche.diabetique,
                "temperature": fiche.temperature,
                "tension_arterielle": fiche.tension_arterielle,
                "pouls": fiche.pouls,
                "has_diagnostic_ia": bool(fiche.diagnostic_ia),
                "has_diagnostic_medecin": bool(fiche.diagnostic),
                "created_at": fiche.created_at,
            }

            # Ajouter données personnelles si autorisé
            if export_job.include_personal_data:
                row.update(
                    {
                        "nom": fiche.nom,
                        "prenom": fiche.prenom,
                        "telephone": fiche.telephone,
                        "adresse": f"{fiche.avenue}, {fiche.quartier}, {fiche.commune}",
                    }
                )

            data.append(row)

        # Créer le DataFrame
        df = pd.DataFrame(data)
        export_job.records_count = len(df)

        # Créer le répertoire d'export s'il n'existe pas
        export_dir = os.path.join(settings.MEDIA_ROOT, "exports")
        os.makedirs(export_dir, exist_ok=True)

        # Générer le nom de fichier
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_consultations_{timestamp}.{export_job.export_format}"
        file_path = os.path.join(export_dir, filename)

        # Exporter selon le format
        if export_job.export_format == "csv":
            df.to_csv(file_path, index=False, encoding="utf-8")
        elif export_job.export_format == "parquet":
            df.to_parquet(file_path, index=False)
        elif export_job.export_format == "json":
            df.to_json(file_path, orient="records", date_format="iso")
        elif export_job.export_format == "excel":
            df.to_excel(file_path, index=False)

        # Finaliser le job
        export_job.file_path = file_path
        export_job.file_size = os.path.getsize(file_path)
        export_job.status = DataExportJob.ExportStatus.COMPLETED
        export_job.completed_at = timezone.now()
        export_job.save()

        return {"status": "completed", "records_count": export_job.records_count, "file_size": export_job.file_size}

    except DataExportJob.DoesNotExist:
        return {"status": "error", "message": "Job not found"}
    except Exception as exc:
        # Marquer le job comme échoué
        try:
            export_job = DataExportJob.objects.get(id=export_job_id)
            export_job.status = DataExportJob.ExportStatus.FAILED
            export_job.error_message = str(exc)
            export_job.completed_at = timezone.now()
            export_job.save()
        except:
            pass

        self.update_state(state="FAILURE", meta={"error": str(exc), "status": "Erreur lors de l'export"})
        raise Ignore()
