#!/usr/bin/env python
"""
Script pour vérifier les informations du médecin
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agent_medical_ia.settings')
django.setup()

from chat.models import FicheConsultation
from authentication.models import CustomUser

def check_medecin_info():
    print("🔍 VÉRIFICATION INFORMATIONS MÉDECIN")
    print("=" * 50)
    
    # 1. Fiche de consultation
    fiche = FicheConsultation.objects.first()
    if not fiche:
        print("❌ Aucune fiche trouvée")
        return
        
    print(f"📋 Fiche ID: {fiche.id}")
    print(f"Patient: {fiche.nom} {fiche.prenom}")
    
    # 2. Médecin assigné
    if fiche.assigned_medecin:
        medecin = fiche.assigned_medecin
        print(f"\n👨‍⚕️ Médecin assigné:")
        print(f"   Nom: {medecin.get_full_name()}")
        print(f"   Username: {medecin.username}")
        print(f"   Email: {medecin.email}")
        
        # 3. Recherche du téléphone
        phone_found = False
        
        # Vérifier profil UserProfileMedecin
        try:
            profile = medecin.userprofilemedecin
            print(f"   Profil médecin trouvé: {profile}")
            if hasattr(profile, 'phone') and profile.phone:
                print(f"   📞 Téléphone (profil): {profile.phone}")
                phone_found = True
        except:
            print("   Pas de profil UserProfileMedecin")
        
        # Vérifier attribut phone direct
        if hasattr(medecin, 'phone') and medecin.phone:
            print(f"   📞 Téléphone (direct): {medecin.phone}")
            phone_found = True
            
        # Vérifier tous les attributs contenant "phone"
        phone_attrs = [attr for attr in dir(medecin) if 'phone' in attr.lower() and not attr.startswith('_')]
        if phone_attrs:
            print(f"   Attributs téléphone: {phone_attrs}")
            for attr in phone_attrs:
                try:
                    value = getattr(medecin, attr)
                    if value:
                        print(f"   📞 {attr}: {value}")
                        phone_found = True
                except:
                    pass
                    
        if not phone_found:
            print("   ❌ Aucun numéro de téléphone trouvé")
            
    else:
        print("❌ Aucun médecin assigné")
    
    # 4. Tous les médecins disponibles
    print(f"\n👥 Tous les médecins:")
    medecins = CustomUser.objects.filter(role='medecin')
    for med in medecins:
        phone = "Non renseigné"
        try:
            if hasattr(med, 'userprofilemedecin') and med.userprofilemedecin.phone:
                phone = med.userprofilemedecin.phone
            elif hasattr(med, 'phone') and med.phone:
                phone = med.phone
        except:
            pass
        print(f"   {med.get_full_name()} ({med.username}) - 📞 {phone}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    check_medecin_info()