from django import forms
from .models import FicheConsultation


class FicheConsultationForm(forms.ModelForm):
    PRESENT_CHOICES = [
        ('patient', 'Patient'),
        ('proche', 'Proche aidant'),
        ('soignant', 'Soignant'),
        ('medecin', 'Médecin'),
        ('autre', 'Autre'),
    ]

    class Meta:
        model = FicheConsultation
        fields = [
            # Patient
            "nom", "postnom", "prenom", "date_naissance", "age", "telephone", "etat_civil",
            "occupation", "sexe", "avenue", "quartier", "commune",
            "contact_nom", "contact_telephone", "contact_adresse",

            # Signes Vitaux
            "temperature", "spo2", "poids", "tension_arterielle", "pouls", "frequence_respiratoire",
            "patient", "proche", "soignant", "medecin", "autre", "proche_lien", "soignant_role", "autre_precisions",

            # Anamnèse
            'motif_consultation', 'histoire_maladie',
            "maison_medicaments", "pharmacie_medicaments", "centre_sante_medicaments", "hopital_medicaments", "medicaments_non_pris",
            'details_medicaments', 'cephalees', 'vertiges', 'palpitations', 'troubles_visuels', 'nycturie',

            # Antécédents médicaux
            'diabetique', 'epileptique', 'trouble_comportement', 'gastritique',
            'hypertendu', 'tabac', 'alcool', 'activite_physique',
            'activite_physique_detail', 'alimentation_habituelle', 'allergie_medicamenteuse', 'medicament_allergique',
            'familial_drepanocytaire', 'familial_diabetique', 'familial_obese', 'familial_hypertendu', 'familial_trouble_comportement',
            'lien_pere', 'lien_mere', 'lien_frere', 'lien_soeur',
             'evenement_traumatique', 'trauma_divorce', 'trauma_perte_parent', 'trauma_deces_epoux', 'trauma_deces_enfant',
            'etat_general', 'autres_antecedents',

            # Examen physique
            'etat', 'par_quoi',
            'capacite_physique', 'capacite_physique_score',
            'capacite_psychologique', 'capacite_psychologique_score',

            'febrile', 'coloration_bulbaire',
            'coloration_palpebrale', 'tegument',

            'tete', 'cou', 'paroi_thoracique', 'poumons',
            'coeur', 'epigastre_hypochondres', 'peri_ombilical_flancs',
            'hypogastre_fosses_iliaques', 'membres', 'colonne_bassin',
            'examen_gynecologique',

            'preoccupations', 'comprehension',
            'attentes', 'engagement',

        ]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "w-full px-4 py-2 border rounded-lg bg-gray-50", "id": "nom"}),
            "postnom": forms.TextInput(
                attrs={"class": "w-full px-4 py-2 border rounded-lg bg-gray-50", "id": "postnom"}),
            "prenom": forms.TextInput(attrs={"class": "w-full px-4 py-2 border rounded-lg bg-gray-50", "id": "prenom"}),
            "date_naissance": forms.DateInput(
                attrs={"type": "date", "class": "w-full px-4 py-2 border rounded-lg bg-gray-50",
                       "id": "date-naissance"}),
            "age": forms.NumberInput(
                attrs={"class": "w-full px-4 py-2 border rounded-lg bg-gray-50", "min": 0, "max": 100, "id": "age"}),
            "telephone": forms.TextInput(
                attrs={"type": "tel", "class": "w-full px-4 py-2 border rounded-lg bg-gray-50", "id": "telephone"}),
            "etat_civil": forms.Select(
                attrs={"class": "w-full px-4 py-2 border rounded-lg bg-gray-50", "id": "etat-civil"}),
            "occupation": forms.TextInput(
                attrs={"class": "w-full px-4 py-2 border rounded-lg bg-gray-50", "id": "occupation"}),
            "sexe": forms.Select(
                choices=[('M', 'Masculin'), ('F', 'Féminin')],
                attrs={"class": "w-full px-4 py-2 border rounded-lg bg-gray-50", "id": "sexe"}),
            "avenue": forms.TextInput(
                attrs={"class": "px-4 py-2 border rounded-lg bg-gray-50", "placeholder": "Avenue", "id": "avenue"}),
            "quartier": forms.TextInput(
                attrs={"class": "px-4 py-2 border rounded-lg bg-gray-50", "placeholder": "Quartier", "id": "quartier"}),
            "commune": forms.TextInput(
                attrs={"class": "px-4 py-2 border rounded-lg bg-gray-50", "placeholder": "Commune", "id": "commune"}),
            "contact_nom": forms.TextInput(
                attrs={"class": "px-4 py-2 border rounded-lg bg-gray-50", "placeholder": "Nom", "id": "contact-nom"}),
            "contact_telephone": forms.TextInput(
                attrs={"type": "tel", "class": "px-4 py-2 border rounded-lg bg-gray-50", "placeholder": "Téléphone",
                       "id": "contact-telephone"}),
            "contact_adresse": forms.TextInput(
                attrs={"class": "px-4 py-2 border rounded-lg bg-gray-50", "placeholder": "Adresse",
                       "id": "contact-adresse"}),

            # Signes vitaux
            "temperature": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg bg-gray-50",
                    "step": "0.1",
                    "min": 30,
                    "max": 45
                }
            ),
            "spo2": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg bg-gray-50",
                    "min": 50,
                    "max": 100
                }
            ),
            "poids": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg bg-gray-50",
                    "min": 1,
                    "max": 300
                }
            ),
            "tension_arterielle": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg bg-gray-50",
                    "placeholder": "ex: 120/80"
                }
            ),
            "pouls": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg bg-gray-50",
                    "min": 30,
                    "max": 200
                }
            ),
            "frequence_respiratoire": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 py-2 border rounded-lg bg-gray-50",
                    "min": 5,
                    "max": 60
                }
            ),

            # Présence à la consultation
            "patient": forms.CheckboxInput(
                attrs={"class": "h-5 w-5 text-blue-600"}
            ),
            "proche": forms.CheckboxInput(
                attrs={"class": "h-5 w-5 text-blue-600"}
            ),
            "soignant": forms.CheckboxInput(
                attrs={"class": "h-5 w-5 text-blue-600"}
            ),
            "medecin": forms.CheckboxInput(
                attrs={"class": "h-5 w-5 text-blue-600"}
            ),
            "autre": forms.CheckboxInput(
                attrs={"class": "h-5 w-5 text-blue-600"}
            ),
            "proche_lien": forms.TextInput(
                attrs={
                    "class": "ml-2 px-2 py-1 border rounded w-24",
                    "placeholder": "lien"
                }
            ),
            "soignant_role": forms.TextInput(
                attrs={
                    "class": "ml-2 px-2 py-1 border rounded w-24",
                    "placeholder": "rôle"
                }
            ),
            "autre_precisions": forms.TextInput(
                attrs={
                    "class": "ml-2 px-2 py-1 border rounded w-24",
                    "placeholder": "préciser"
                }
            ),

            # Anamnèse
            'motif_consultation': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50',
                'rows': 3
            }),
            'histoire_maladie': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50',
                'rows': 5
            }),
            "maison_medicaments": forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),
            "pharmacie_medicaments": forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),
            "centre_sante_medicaments": forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),
            "hopital_medicaments": forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),
            "medicaments_non_pris": forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),
            'details_medicaments': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50',
                'rows': 2
            }),
            'cephalees': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),
            'vertiges': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),
            'palpitations': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),
            'troubles_visuels': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),
            'nycturie': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),

            # Antécédents médicaux
            'hypertendu': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),
            'diabetique': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),
            'epileptique': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),
            'trouble_comportement': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),
            'gastritique': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),

            'tabac': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50'
            }),
            'alcool': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50'
            }),
            'activite_physique': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50'
            }),
            'activite_physique_detail': forms.TextInput(attrs={
                'class': 'w-full mt-2 px-4 py-2 border rounded-lg bg-gray-50',
                'placeholder': 'Quelles activités?'
            }),
            'alimentation_habituelle': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50',
                'rows': 2
            }),

            'allergie_medicamenteuse': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),
            'medicament_allergique': forms.TextInput(attrs={
                'class': 'ml-4 px-4 py-2 border rounded-lg bg-gray-50 flex-grow',
                'placeholder': 'Médicament allergique'
            }),

            'familial_drepanocytaire': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),
            'familial_diabetique': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),
            'familial_obese': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),
            'familial_hypertendu': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),
            'familial_trouble_comportement': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),

            'lien_pere': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),
            'lien_mere': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),
            'lien_frere': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),
            'lien_soeur': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),

            'evenement_traumatique': forms.RadioSelect(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),
            'trauma_divorce': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),
            'trauma_perte_parent': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),
            'trauma_deces_epoux': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),
            'trauma_deces_enfant': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600'
            }),

            'etat_general': forms.TextInput(attrs={'class': 'w-full mt-2 px-4 py-2 border rounded-lg bg-gray-50'}),
            'autres_antecedents': forms.TextInput(
                attrs={'class': 'w-full mt-2 px-4 py-2 border rounded-lg bg-gray-50'}),
            # Examen physique
            'etat': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50'}),
            'par_quoi': forms.TextInput(
                attrs={'class': 'w-full mt-2 px-4 py-2 border rounded-lg bg-gray-50', 'placeholder': 'Par quoi?'}),

            'capacite_physique': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50'}),
            'capacite_physique_score': forms.TextInput(
                attrs={'class': 'w-full mt-2 px-4 py-2 border rounded-lg bg-gray-50', 'placeholder': '8/10'}),

            'capacite_psychologique': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50'}),
            'capacite_psychologique_score': forms.TextInput(
                attrs={'class': 'w-full mt-2 px-4 py-2 border rounded-lg bg-gray-50', 'placeholder': '8/10'}),

            'febrile': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50'}),
            'coloration_bulbaire': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50'}),
            'coloration_palpebrale': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50'}),
            'tegument': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50'}),

            'tete': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50'}),
            'cou': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50'}),
            'paroi_thoracique': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50'}),
            'poumons': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50'}),
            'coeur': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50'}),
            'epigastre_hypochondres': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50'}),
            'peri_ombilical_flancs': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50'}),
            'hypogastre_fosses_iliaques': forms.Textarea(
                attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50'}),
            'membres': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50'}),
            'colonne_bassin': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50'}),
            'examen_gynecologique': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50'}),

            'preoccupations': forms.Textarea(
                attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50', 'rows': 2}),
            'comprehension': forms.Textarea(
                attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50', 'rows': 2}),
            'attentes': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50', 'rows': 2}),
            'engagement': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50', 'rows': 2}),
            'commentaire_medecin' : forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg bg-gray-50', 'rows': 2})
        }
