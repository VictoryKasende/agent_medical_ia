from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),

    path('', views.AnalyseSymptomesView.as_view(), name='home'),
    path('analyse/', views.AnalyseSymptomesView.as_view(), name='analyse'),  
    path("consultation/", views.FicheConsultationCreateView.as_view(), name="consultation"),
    path('chat/history/', views.ChatHistoryView.as_view(), name='chat_history'),
    path('diagnostic-result/', views.diagnostic_result, name='diagnostic_result'),

    path('conversation/', views.ConversationView.as_view()),  # POST (création)
    path('conversation/<int:conversation_id>/', views.ConversationView.as_view()),  # GET/DELETE
]