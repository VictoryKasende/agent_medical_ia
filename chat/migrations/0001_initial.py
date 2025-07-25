# Generated by Django 5.2 on 2025-07-15 22:09

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FicheConsultation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100)),
                ('postnom', models.CharField(max_length=100)),
                ('prenom', models.CharField(max_length=100)),
                ('date_naissance', models.DateField()),
                ('age', models.IntegerField()),
                ('sexe', models.CharField(choices=[('M', 'Masculin'), ('F', 'Féminin')], max_length=10, null=True)),
                ('telephone', models.CharField(max_length=30)),
                ('etat_civil', models.CharField(choices=[('Célibataire', 'Célibataire'), ('Marié(e)', 'Marié(e)'), ('Divorcé(e)', 'Divorcé(e)'), ('Veuf(ve)', 'Veuf(ve)')], default='Célibataire', max_length=30)),
                ('occupation', models.CharField(max_length=100)),
                ('avenue', models.CharField(max_length=100)),
                ('quartier', models.CharField(max_length=100)),
                ('commune', models.CharField(max_length=100)),
                ('contact_nom', models.CharField(max_length=100)),
                ('contact_telephone', models.CharField(max_length=30)),
                ('contact_adresse', models.CharField(max_length=255)),
                ('date_consultation', models.DateField(auto_now_add=True)),
                ('heure_debut', models.TimeField(blank=True, null=True)),
                ('heure_fin', models.TimeField(blank=True, null=True)),
                ('numero_dossier', models.CharField(blank=True, max_length=50, unique=True)),
                ('temperature', models.FloatField(blank=True, help_text='Température en °C', null=True)),
                ('spo2', models.IntegerField(blank=True, help_text='Saturation en oxygène (%)', null=True)),
                ('poids', models.FloatField(blank=True, help_text='Poids en kg', null=True)),
                ('tension_arterielle', models.CharField(blank=True, help_text='Ex: 120/80', max_length=20, null=True)),
                ('pouls', models.IntegerField(blank=True, help_text='Pouls (battements/minute)', null=True)),
                ('frequence_respiratoire', models.IntegerField(blank=True, help_text='FR (mouvements/minute)', null=True)),
                ('patient', models.BooleanField(default=True, help_text='Le patient est-il présent ?')),
                ('proche', models.BooleanField(default=False, help_text='Un proche est-il présent ?')),
                ('soignant', models.BooleanField(default=False, help_text='Un soignant est-il présent ?')),
                ('medecin', models.BooleanField(default=False, help_text='Un médecin est-il présent ?')),
                ('autre', models.BooleanField(default=False, help_text='Un autre intervenant est-il présent ?')),
                ('proche_lien', models.CharField(blank=True, max_length=100, null=True)),
                ('soignant_role', models.CharField(blank=True, max_length=100, null=True)),
                ('autre_precisions', models.CharField(blank=True, max_length=100, null=True)),
                ('motif_consultation', models.TextField(blank=True, null=True)),
                ('histoire_maladie', models.TextField(blank=True, null=True)),
                ('maison_medicaments', models.BooleanField(default=False, help_text='Des médicaments sont-ils pris à la maison ?')),
                ('pharmacie_medicaments', models.BooleanField(default=False, help_text='Des médicaments sont-ils pris à la pharmacie ?')),
                ('centre_sante_medicaments', models.BooleanField(default=False, help_text='Des médicaments sont-ils pris au centre de santé ?')),
                ('hopital_medicaments', models.BooleanField(default=False, help_text="Des médicaments sont-ils pris à l'hôpital ?")),
                ('medicaments_non_pris', models.BooleanField(default=False, help_text="Des médicaments n'ont-ils pas été pris ?")),
                ('details_medicaments', models.TextField(blank=True, null=True)),
                ('cephalees', models.BooleanField(blank=True, default=False, help_text='Le patient a-t-il des céphalées ?', null=True)),
                ('vertiges', models.BooleanField(blank=True, default=False, help_text='Le patient a-t-il des vertiges ?', null=True)),
                ('palpitations', models.BooleanField(blank=True, default=False, help_text='Le patient a-t-il des palpitations ?', null=True)),
                ('troubles_visuels', models.BooleanField(blank=True, default=False, help_text='Le patient a-t-il des troubles visuels ?', null=True)),
                ('nycturie', models.BooleanField(blank=True, default=False, help_text='Le patient a-t-il des nycturies ?', null=True)),
                ('hypertendu', models.BooleanField(default=False)),
                ('diabetique', models.BooleanField(default=False)),
                ('epileptique', models.BooleanField(default=False)),
                ('trouble_comportement', models.BooleanField(default=False)),
                ('gastritique', models.BooleanField(default=False)),
                ('tabac', models.CharField(choices=[('non', 'Non'), ('rarement', 'Rarement'), ('souvent', 'Souvent'), ('tres_souvent', 'Très souvent')], default='non', max_length=20)),
                ('alcool', models.CharField(choices=[('non', 'Non'), ('rarement', 'Rarement'), ('souvent', 'Souvent'), ('tres_souvent', 'Très souvent')], default='non', max_length=20)),
                ('activite_physique', models.CharField(choices=[('non', 'Non'), ('rarement', 'Rarement'), ('souvent', 'Souvent'), ('tres_souvent', 'Très souvent')], default='rarement', max_length=20)),
                ('activite_physique_detail', models.TextField(blank=True, null=True)),
                ('alimentation_habituelle', models.TextField(blank=True, null=True)),
                ('allergie_medicamenteuse', models.BooleanField(default=False)),
                ('medicament_allergique', models.CharField(blank=True, max_length=255, null=True)),
                ('familial_drepanocytaire', models.BooleanField(default=False)),
                ('familial_diabetique', models.BooleanField(default=False)),
                ('familial_obese', models.BooleanField(default=False)),
                ('familial_hypertendu', models.BooleanField(default=False)),
                ('familial_trouble_comportement', models.BooleanField(default=False)),
                ('lien_pere', models.BooleanField(default=False)),
                ('lien_mere', models.BooleanField(default=False)),
                ('lien_frere', models.BooleanField(default=False)),
                ('lien_soeur', models.BooleanField(default=False)),
                ('evenement_traumatique', models.CharField(choices=[('oui', 'Oui'), ('non', 'Non'), ('inconnu', 'Je ne sais pas')], default='non', max_length=10)),
                ('trauma_divorce', models.BooleanField(default=False)),
                ('trauma_perte_parent', models.BooleanField(default=False)),
                ('trauma_deces_epoux', models.BooleanField(default=False)),
                ('trauma_deces_enfant', models.BooleanField(default=False)),
                ('etat_general', models.TextField(blank=True, max_length=255, null=True)),
                ('autres_antecedents', models.TextField(blank=True, max_length=255, null=True)),
                ('etat', models.CharField(choices=[('Conservé', 'Conservé'), ('Altéré', 'Altéré')], max_length=20)),
                ('par_quoi', models.TextField(blank=True, max_length=255, null=True)),
                ('capacite_physique', models.CharField(choices=[('Top', 'Top'), ('Moyen', 'Moyen'), ('Bas', 'Bas')], max_length=20)),
                ('capacite_physique_score', models.CharField(blank=True, max_length=10, null=True)),
                ('capacite_psychologique', models.CharField(choices=[('Top', 'Top'), ('Moyen', 'Moyen'), ('Bas', 'Bas')], max_length=20)),
                ('capacite_psychologique_score', models.CharField(blank=True, max_length=10, null=True)),
                ('febrile', models.CharField(choices=[('Oui', 'Oui'), ('Non', 'Non')], max_length=10)),
                ('coloration_bulbaire', models.CharField(choices=[('Normale', 'Normale'), ('Anormale', 'Anormale')], max_length=20)),
                ('coloration_palpebrale', models.CharField(choices=[('Normale', 'Normale'), ('Anormale', 'Anormale')], max_length=20)),
                ('tegument', models.CharField(choices=[('Normal', 'Normal'), ('Anormal', 'Anormal')], max_length=20)),
                ('tete', models.TextField(blank=True, null=True)),
                ('cou', models.TextField(blank=True, null=True)),
                ('paroi_thoracique', models.TextField(blank=True, null=True)),
                ('poumons', models.TextField(blank=True, null=True)),
                ('coeur', models.TextField(blank=True, null=True)),
                ('epigastre_hypochondres', models.TextField(blank=True, null=True)),
                ('peri_ombilical_flancs', models.TextField(blank=True, null=True)),
                ('hypogastre_fosses_iliaques', models.TextField(blank=True, null=True)),
                ('membres', models.TextField(blank=True, null=True)),
                ('colonne_bassin', models.TextField(blank=True, null=True)),
                ('examen_gynecologique', models.TextField(blank=True, null=True)),
                ('preoccupations', models.TextField(blank=True, null=True)),
                ('comprehension', models.TextField(blank=True, null=True)),
                ('attentes', models.TextField(blank=True, null=True)),
                ('engagement', models.TextField(blank=True, null=True)),
                ('is_patient_distance', models.BooleanField(default=False)),
                ('status', models.CharField(choices=[('en_analyse', "En cours d'analyse"), ('analyse_terminee', 'Analyse terminée'), ('valide_medecin', 'Validé par médecin'), ('rejete_medecin', 'Rejeté par médecin')], default='en_analyse', max_length=20)),
                ('diagnostic', models.TextField(blank=True, null=True)),
                ('traitement', models.TextField(blank=True, null=True)),
                ('examen_complementaire', models.TextField(blank=True, null=True)),
                ('recommandations', models.TextField(blank=True, null=True)),
                ('date_validation', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('diagnostic_ia', models.TextField(blank=True, null=True)),
                ('signature_medecin', models.ImageField(blank=True, help_text='Signature du médecin pour valider la consultation', null=True, upload_to='signatures/')),
                ('medecin_validateur', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='consultations_validees', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Fiche de Consultation',
                'verbose_name_plural': 'Fiches de Consultation',
                'ordering': ['-date_consultation'],
            },
        ),
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(blank=True, max_length=100, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conversations', to=settings.AUTH_USER_MODEL)),
                ('fiche', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='conversations', to='chat.ficheconsultation')),
            ],
            options={
                'verbose_name': 'Conversation',
                'verbose_name_plural': 'Conversations',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='MessageIA',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('user', 'Utilisateur'), ('gpt4', 'GPT-4'), ('claude', 'Claude 3'), ('gemini', 'Gemini Pro'), ('synthese', 'Synthèse Finale')], max_length=20)),
                ('content', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chat.conversation')),
            ],
            options={
                'verbose_name': 'Message IA',
                'verbose_name_plural': 'Messages IA',
                'ordering': ['timestamp'],
            },
        ),
    ]
