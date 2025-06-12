from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Conversation, MessageIA, FicheConsultation, UserProfile
from django.db.models.signals import post_save
from django.dispatch import receiver


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

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profil utilisateur'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)

# Désenregistre User puis réenregistre-le avec l’inline
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        # Crée le profil s'il n'existe pas (cas d'utilisateurs déjà présents)
        profile, created = UserProfile.objects.get_or_create(user=instance)
        profile.save()
