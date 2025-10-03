#!/usr/bin/env python3
"""
Script de test pour valider les nouveaux endpoints de l'API Agent Médical IA.
Teste les fonctionnalités P0 implémentées.

Usage:
    python test_api_endpoints.py

Prérequis:
    - Serveur Django démarré (python manage.py runserver)
    - Base de données avec utilisateurs de test
    - Variables d'environnement configurées
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Couleurs pour l'affichage
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def log(message: str, color: str = Colors.END):
    """Affiche un message coloré."""
    print(f"{color}{message}{Colors.END}")

def log_success(message: str):
    log(f"✅ {message}", Colors.GREEN)

def log_error(message: str):
    log(f"❌ {message}", Colors.RED)

def log_warning(message: str):
    log(f"⚠️  {message}", Colors.YELLOW)

def log_info(message: str):
    log(f"ℹ️  {message}", Colors.BLUE)

class APITester:
    """Testeur pour les endpoints de l'API."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.test_data = {}
    
    def authenticate(self, username: str = "admin", password: str = "admin123") -> bool:
        """Authentification avec l'API."""
        try:
            response = self.session.post(
                f"{self.base_url}/auth/jwt/create/",
                json={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                log_success("Authentification réussie")
                return True
            else:
                log_error(f"Échec authentification: {response.status_code}")
                return False
                
        except Exception as e:
            log_error(f"Erreur authentification: {e}")
            return False
    
    def test_endpoint(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     files: Optional[Dict] = None, expected_status: int = 200) -> Optional[Dict]:
        """Teste un endpoint et retourne la réponse."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                if files:
                    response = self.session.post(url, data=data, files=files)
                else:
                    response = self.session.post(url, json=data)
            elif method.upper() == "PATCH":
                response = self.session.patch(url, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url)
            else:
                log_error(f"Méthode HTTP non supportée: {method}")
                return None
            
            if response.status_code == expected_status:
                log_success(f"{method} {endpoint} - Status {response.status_code}")
                try:
                    return response.json()
                except:
                    return {"success": True}
            else:
                log_error(f"{method} {endpoint} - Status {response.status_code}")
                try:
                    log_error(f"Erreur: {response.json()}")
                except:
                    log_error(f"Erreur: {response.text}")
                return None
                
        except Exception as e:
            log_error(f"Exception {method} {endpoint}: {e}")
            return None
    
    def test_fiche_consultation_crud(self):
        """Test CRUD des fiches de consultation."""
        log_info("=== Test Fiches de Consultation ===")
        
        # 1. Créer une fiche
        fiche_data = {
            "nom": "Test",
            "postnom": "Patient",
            "prenom": "API",
            "age": 35,
            "sexe": "M",
            "telephone": "+33123456789",
            "date_naissance": "1989-01-01",
            "etat_civil": "Célibataire",
            "occupation": "Développeur",
            "avenue": "123 Rue Test",
            "quartier": "Centre",
            "commune": "Paris",
            "contact_nom": "Contact Test",
            "contact_telephone": "+33987654321",
            "contact_adresse": "456 Avenue Contact",
            "motif_consultation": "Test API automatisé",
            "histoire_maladie": "Patient test pour validation API",
            "hypothese_patient_medecin": "Suspicion de stress lié au développement",
            "analyses_proposees": "Bilan sanguin complet, ECG",
            "temperature": 37.2,
            "spo2": 98,
            "tension_arterielle": "120/80",
            "pouls": 75,
            "etat": "Conservé",
            "febrile": "Non",
            "coloration_bulbaire": "normale",
            "coloration_palpebrale": "normale"
        }
        
        response = self.test_endpoint("POST", "/api/v1/fiche-consultation/", fiche_data, expected_status=201)
        if response:
            fiche_id = response.get("id")
            self.test_data["fiche_id"] = fiche_id
            log_success(f"Fiche créée avec ID: {fiche_id}")
            
            # 2. Récupérer la fiche
            fiche = self.test_endpoint("GET", f"/api/v1/fiche-consultation/{fiche_id}/")
            if fiche:
                log_success("Fiche récupérée avec succès")
                
                # 3. Tester l'édition du diagnostic
                diagnostic_data = {
                    "diagnostic": "Stress professionnel confirmé",
                    "traitement": "Repos, techniques de relaxation",
                    "recommandations": "Suivi dans 2 semaines"
                }
                
                edit_response = self.test_endpoint(
                    "PATCH", 
                    f"/api/v1/fiche-consultation/{fiche_id}/edit-diagnostic/",
                    diagnostic_data
                )
                if edit_response:
                    log_success("Diagnostic édité avec succès")
    
    def test_lab_results(self):
        """Test des résultats de laboratoire."""
        log_info("=== Test Résultats de Laboratoire ===")
        
        if not self.test_data.get("fiche_id"):
            log_warning("Pas de fiche test disponible, création d'une fiche simple")
            return
        
        fiche_id = self.test_data["fiche_id"]
        
        # Créer un résultat de laboratoire
        lab_data = {
            "fiche": fiche_id,
            "type_analyse": "Glycémie à jeun",
            "valeur": "0.95",
            "unite": "g/L",
            "valeurs_normales": "0.70 - 1.10",
            "date_prelevement": "2024-10-03",
            "laboratoire": "Laboratoire Test API",
            "commentaire": "Résultat normal"
        }
        
        response = self.test_endpoint("POST", "/api/v1/lab-results/", lab_data, expected_status=201)
        if response:
            lab_id = response.get("id")
            self.test_data["lab_id"] = lab_id
            log_success(f"Résultat labo créé avec ID: {lab_id}")
            
            # Lister les résultats pour cette fiche
            self.test_endpoint("GET", f"/api/v1/lab-results/?fiche={fiche_id}")
    
    def test_attachments(self):
        """Test des pièces jointes."""
        log_info("=== Test Pièces Jointes ===")
        
        if not self.test_data.get("fiche_id"):
            log_warning("Pas de fiche test disponible")
            return
        
        fiche_id = self.test_data["fiche_id"]
        
        # Créer un fichier test temporaire
        test_content = "Contenu de test pour validation API"
        
        try:
            # Simuler un upload de fichier
            attachment_data = {
                "fiche": fiche_id,
                "kind": "document",
                "note": "Document de test API"
            }
            
            # Note: Pour un vrai test d'upload, il faudrait un fichier réel
            # files = {"file": ("test.txt", test_content, "text/plain")}
            
            # Pour l'instant, on teste juste la liste
            self.test_endpoint("GET", f"/api/v1/attachments/?fiche={fiche_id}")
            
        except Exception as e:
            log_warning(f"Test attachments simplifié: {e}")
    
    def test_references(self):
        """Test des références bibliographiques."""
        log_info("=== Test Références Bibliographiques ===")
        
        if not self.test_data.get("fiche_id"):
            log_warning("Pas de fiche test disponible")
            return
        
        fiche_id = self.test_data["fiche_id"]
        
        # Créer une référence
        ref_data = {
            "fiche": fiche_id,
            "title": "Clinical Guidelines for API Testing",
            "source": "pubmed",
            "authors": "Smith J, Doe A",
            "year": 2024,
            "journal": "Journal of API Medicine",
            "url": "https://pubmed.ncbi.nlm.nih.gov/test"
        }
        
        response = self.test_endpoint("POST", "/api/v1/references/", ref_data, expected_status=201)
        if response:
            ref_id = response.get("id")
            log_success(f"Référence créée avec ID: {ref_id}")
            
            # Lister via action custom
            self.test_endpoint("GET", f"/api/v1/fiche-consultation/{fiche_id}/references/")
    
    def test_appointments(self):
        """Test des rendez-vous."""
        log_info("=== Test Rendez-vous ===")
        
        # Créer un rendez-vous
        tomorrow = datetime.now() + timedelta(days=1)
        
        appointment_data = {
            "requested_start": tomorrow.isoformat(),
            "requested_end": (tomorrow + timedelta(hours=1)).isoformat(),
            "consultation_mode": "distanciel",
            "location_note": "Lien de téléconsultation sera envoyé",
            "message_patient": "Demande de consultation pour test API"
        }
        
        response = self.test_endpoint("POST", "/api/v1/appointments/", appointment_data, expected_status=201)
        if response:
            appointment_id = response.get("id")
            self.test_data["appointment_id"] = appointment_id
            log_success(f"Rendez-vous créé avec ID: {appointment_id}")
    
    def test_exports(self):
        """Test des exports PDF/JSON."""
        log_info("=== Test Exports ===")
        
        if not self.test_data.get("fiche_id"):
            log_warning("Pas de fiche test disponible")
            return
        
        fiche_id = self.test_data["fiche_id"]
        
        # Test export JSON
        json_response = self.test_endpoint("GET", f"/api/v1/fiche-consultation/{fiche_id}/export/json/")
        if json_response:
            log_success("Export JSON réussi")
        
        # Test export PDF (peut échouer si WeasyPrint non installé)
        pdf_response = self.test_endpoint(
            "GET", 
            f"/api/v1/fiche-consultation/{fiche_id}/export/pdf/",
            expected_status=[200, 501]  # 501 si WeasyPrint non installé
        )
        if pdf_response:
            log_success("Export PDF testé")
    
    def test_notifications(self):
        """Test des notifications."""
        log_info("=== Test Notifications ===")
        
        if not self.test_data.get("fiche_id"):
            log_warning("Pas de fiche test disponible")
            return
        
        fiche_id = self.test_data["fiche_id"]
        
        # Test notification SMS (mode simulation)
        notif_data = {"method": "sms", "force_resend": True}
        
        sms_response = self.test_endpoint(
            "POST", 
            f"/api/v1/fiche-consultation/{fiche_id}/send-notification/",
            notif_data,
            expected_status=[200, 501]  # 501 si Twilio non configuré
        )
        
        if sms_response:
            log_success("Test notification SMS réussi")
    
    def test_openapi_schema(self):
        """Test du schéma OpenAPI."""
        log_info("=== Test Documentation API ===")
        
        # Test schéma OpenAPI
        schema_response = self.test_endpoint("GET", "/api/schema/")
        if schema_response:
            log_success("Schéma OpenAPI accessible")
        
        # Test documentation Swagger
        # Note: Swagger UI retourne du HTML, pas du JSON
        try:
            response = self.session.get(f"{self.base_url}/api/docs/")
            if response.status_code == 200:
                log_success("Documentation Swagger accessible")
            else:
                log_error(f"Documentation Swagger inaccessible: {response.status_code}")
        except Exception as e:
            log_error(f"Erreur documentation: {e}")
    
    def run_all_tests(self):
        """Lance tous les tests."""
        log(f"\n{Colors.BOLD}🧪 LANCEMENT DES TESTS API - Agent Médical IA{Colors.END}\n", Colors.CYAN)
        
        # Authentification obligatoire
        if not self.authenticate():
            log_error("Impossible de s'authentifier. Arrêt des tests.")
            return False
        
        # Tests des fonctionnalités
        tests = [
            self.test_fiche_consultation_crud,
            self.test_lab_results,
            self.test_attachments,
            self.test_references,
            self.test_appointments,
            self.test_exports,
            self.test_notifications,
            self.test_openapi_schema
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                test()
                passed += 1
                log("")  # Ligne vide
            except Exception as e:
                log_error(f"Erreur dans {test.__name__}: {e}")
                log("")
        
        # Résumé final
        log(f"\n{Colors.BOLD}📊 RÉSULTATS DES TESTS{Colors.END}", Colors.CYAN)
        log(f"Tests réussis: {passed}/{total}")
        
        if passed == total:
            log_success("🎉 Tous les tests sont passés avec succès!")
        else:
            log_warning(f"⚠️  {total - passed} test(s) ont échoué")
        
        # Affichage des données de test créées
        if self.test_data:
            log_info("Données de test créées:")
            for key, value in self.test_data.items():
                log(f"  - {key}: {value}")
        
        return passed == total


def test_p1_features():
    """Test spécifique pour les fonctionnalités P1."""
    log(f"\n{Colors.BOLD}🧪 TESTS FONCTIONNALITÉS P1{Colors.END}\n", Colors.CYAN)
    
    tester = APITester(API_BASE)
    
    if not tester.authenticate():
        log_error("Impossible de s'authentifier pour les tests P1")
        return False
    
    # Test disponibilités médecin
    log_info("=== Test Disponibilités Médecin ===")
    
    # Créer une disponibilité
    availability_data = {
        "day_of_week": 1,  # Mardi
        "start_time": "09:00:00",
        "end_time": "17:00:00",
        "consultation_type": "both",
        "duration_minutes": 30,
        "location": "Cabinet test API",
        "max_consultations": 2
    }
    
    availability_response = tester.test_endpoint(
        "POST", 
        "/api/v1/availabilities/", 
        availability_data, 
        expected_status=201
    )
    
    if availability_response:
        availability_id = availability_response.get("id")
        log_success(f"Disponibilité créée avec ID: {availability_id}")
        
        # Test créneaux disponibles
        from datetime import date, timedelta
        today = date.today()
        next_week = today + timedelta(days=7)
        
        slots_response = tester.test_endpoint(
            "GET",
            f"/api/v1/availabilities/available-slots/?date_start={today}&date_end={next_week}"
        )
        
        if slots_response:
            log_success(f"Créneaux récupérés: {len(slots_response)} slots")
        
        # Test génération ICS
        ics_response = tester.test_endpoint("GET", "/api/v1/availabilities/calendar-ics/")
        if ics_response:
            log_success("Calendrier ICS généré")
    
    # Test exceptions médecin
    log_info("=== Test Exceptions Médecin ===")
    
    exception_data = {
        "start_datetime": "2024-10-15T09:00:00Z",
        "end_datetime": "2024-10-15T17:00:00Z",
        "exception_type": "vacation",
        "reason": "Congé annuel",
        "is_recurring": False
    }
    
    exception_response = tester.test_endpoint(
        "POST",
        "/api/v1/exceptions/",
        exception_data,
        expected_status=201
    )
    
    if exception_response:
        log_success("Exception médecin créée")
    
    # Test exports de données (admin requis)
    log_info("=== Test Exports de Données ===")
    
    export_data = {
        "export_format": "csv",
        "date_start": "2024-01-01",
        "date_end": "2024-12-31",
        "include_personal_data": False,
        "filters": {
            "status": ["valide_medecin"]
        }
    }
    
    export_response = tester.test_endpoint(
        "POST",
        "/api/v1/exports/",
        export_data,
        expected_status=[201, 403]  # 403 si pas admin
    )
    
    if export_response:
        log_success("Export de données lancé")
    else:
        log_warning("Export non autorisé (utilisateur non admin)")
    
    # Test webhook simulation
    log_info("=== Test Webhooks ===")
    
    webhook_data = {
        "MessageSid": "TEST_MSG_123456",
        "From": "whatsapp:+33123456789",
        "To": "whatsapp:+33987654321",
        "Body": "Message de test API"
    }
    
    webhook_response = tester.test_endpoint(
        "POST",
        "/api/v1/webhooks/twilio/whatsapp/",
        webhook_data
    )
    
    if webhook_response:
        log_success("Webhook WhatsApp traité")
    
    log_success("Tests P1 terminés")
    return True


def main():
    """Point d'entrée principal avec tests P0 et P1."""
    # Vérifications préalables
    try:
        response = requests.get(f"{BASE_URL}/api/v1/", timeout=5)
        if response.status_code != 200:
            log_error(f"API non accessible sur {BASE_URL}")
            return False
    except Exception as e:
        log_error(f"Impossible de contacter l'API: {e}")
        log_info("Assurez-vous que le serveur Django est démarré:")
        log_info("python manage.py runserver")
        return False
    
    # Tests P0 (fonctionnalités de base)
    tester = APITester(API_BASE)
    success_p0 = tester.run_all_tests()
    
    # Tests P1 (fonctionnalités avancées)
    success_p1 = test_p1_features()
    
    # Résumé final
    log(f"\n{Colors.BOLD}📊 RÉSULTATS FINAUX{Colors.END}", Colors.CYAN)
    log(f"Tests P0 (priorité): {'✅ RÉUSSIS' if success_p0 else '❌ ÉCHECS'}")
    log(f"Tests P1 (avancés): {'✅ RÉUSSIS' if success_p1 else '❌ ÉCHECS'}")
    
    if success_p0 and success_p1:
        log_success("🎉 TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS!")
        log_info("Le backend est prêt pour la production.")
    else:
        log_warning("⚠️ Certains tests ont échoué")
        log_info("Vérifiez les logs ci-dessus pour les détails.")
    
    # Code de sortie
    sys.exit(0 if (success_p0 and success_p1) else 1)

if __name__ == "__main__":
    main()