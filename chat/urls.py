from django.urls import path
from . import views
from .views import SendWhatsAppMessageView

urlpatterns = [
    path('', views.AnalyseSymptomesView.as_view(), name='analyse'),
    path('check-task-status/<str:task_id>/', views.check_task_status, name='check_task_status'),
    path("consultation/", views.FicheConsultationCreateView.as_view(), name="consultation"),
    path("relancer-analyse/<int:fiche_id>/", views.RelancerAnalyseMedecinView.as_view(), name="relancer_analyse"),
    path('diagnostic-result/', views.diagnostic_result, name='diagnostic_result'),
    path('consultations-distance/', views.ConsultationsDistanceView.as_view(), name='consultations_distance'),
    path('api/consultations-distance/', views.api_consultations_distance, name='api_consultations_distance'),
    path('valider-diagnostic/<int:fiche_id>/', views.valider_diagnostic_medecin, name='valider_diagnostic'),
    path('chat-history-partial/', views.chat_history_partial, name='chat_history_partial'),

    path('dashboard/patient/', views.PatientDashboardView.as_view(), name='patient_dashboard'),
    path('dashboard/medecin/', views.MedecinDashboardView.as_view(), name='medecin_dashboard'),
    path('dashboard/proche/', views.ProcheDashboardView.as_view(), name='proche_dashboard'),
    path('dashboard/', views.redirection_dashboard, name='dashboard_redirect'),

    # Ajout pour API conversation
    path('conversation/', views.ConversationView.as_view()),  # POST (création)
    path('conversation/<int:conversation_id>/', views.ConversationView.as_view()),  # GET/DELETE
    

    # Consultation du patient présent
    path('consultation/patient/', views.ConsultationPatientView.as_view(), name='consultation_patient_present'),
    path('consultation/patient/<int:fiche_id>/modifier/', views.FicheConsultationUpdateView.as_view(), name='fiche_consultation_update'),
    path('consultation/patient/<int:fiche_id>/modifier/statut', views.UpdateFicheStatusView.as_view(), name='fiche_consultation_update_status'),
    path('consultation/patient/<int:fiche_id>/details/', views.FicheConsultationDetailView.as_view(), name='fiche_consultation_detail'),
    path('consultation/<int:pk>/print/', views.PrintConsultationView.as_view(), name='consultation_print'),

    # Consultation du patient distant
    path('consultation/patient-distant/', views.ConsultationPatientDistantView.as_view(), name='consultation_patient_distant'),
    path('consultation/patient-distant/<int:fiche_id>/modifier/', views.FicheConsultationUpdateView.as_view(), name='fiche_consultation_update_distant'),


    # Envoyer un message WhatsApp
    path('send-whatsapp/<int:consultation_id>/', views.send_whatsapp_message_view, name='send_whatsapp_message'),  # ← CHANGÉ
]