from django.urls import path
from . import views
from .views import FicheConsultationCreateView, RelancerAnalyseMedecinView, PatientDashboardView, MedecinDashboardView, ProcheDashboardView

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('', views.AnalyseSymptomesView.as_view(), name='home'),
    path('analyse/', views.AnalyseSymptomesView.as_view(), name='analyse'),
    path('check-task-status/<str:task_id>/', views.check_task_status, name='check_task_status'),
    path("consultation/", FicheConsultationCreateView.as_view(), name="consultation"),
    path("relancer-analyse/<int:fiche_id>/", RelancerAnalyseMedecinView.as_view(), name="relancer_analyse"),
    path('chat/history/', views.ChatHistoryView.as_view(), name='chat_history'),
    path('diagnostic-result/', views.diagnostic_result, name='diagnostic_result'),

    path('consultations-distance/', views.ConsultationsDistanceView.as_view(), name='consultations_distance'),
    path('api/consultations-distance/', views.api_consultations_distance, name='api_consultations_distance'),
    path('valider-diagnostic/<int:fiche_id>/', views.valider_diagnostic_medecin, name='valider_diagnostic'),
    path('dashboard/patient/', PatientDashboardView.as_view(), name='patient_dashboard'),
    path('dashboard/medecin/', MedecinDashboardView.as_view(), name='medecin_dashboard'),
    path('dashboard/proche/', ProcheDashboardView.as_view(), name='proche_dashboard'),
]