from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Conversation, MessageIA, FicheConsultation


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'fiche', 'created_at', 'titre', 'nom')
    list_filter = ('created_at', 'fiche')
    search_fields = ('user__username', 'fiche__numero_dossier')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

@admin.register(MessageIA)
class MessageIAAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'role', 'short_content', 'timestamp')
    list_filter = ('role', 'timestamp')
    search_fields = ('conversation__user__username', 'content')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)

    def short_content(self, obj):
        return (obj.content[:75] + '...') if len(obj.content) > 75 else obj.content
    short_content.short_description = 'Contenu'

@admin.register(FicheConsultation)
class FicheConsultationAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom', 'prenom', 'date_naissance', 'age', 'numero_dossier', 'conversations_count')
    list_filter = ('date_consultation',)
    search_fields = ('nom', 'prenom', 'numero_dossier')
    date_hierarchy = 'date_naissance'
    ordering = ('-date_naissance',)

    def conversations_count(self, obj):
        return obj.conversations.count()
    conversations_count.short_description = "Nb conversations"



