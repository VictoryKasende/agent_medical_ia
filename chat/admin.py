from django.contrib import admin
from .models import Conversation, MessageIA, FicheConsultation


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username',)
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
    list_display = ('id', 'conversation', 'nom', 'prenom', 'date_naissance', 'age')
    list_filter = ('conversation__user',)
    search_fields = ('nom', 'prenom', 'conversation__user__username')
    date_hierarchy = 'date_naissance'
    ordering = ('-date_naissance',)
