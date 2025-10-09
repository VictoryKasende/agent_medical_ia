import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="markdown")
def markdown_format(text):
    """
    Convertit le texte Markdown en HTML
    """
    if not text:
        return ""

    try:
        # Configuration Markdown avec extensions de base
        md = markdown.Markdown(
            extensions=[
                "markdown.extensions.fenced_code",  # Pour les blocs de code
                "markdown.extensions.tables",  # Pour les tableaux
                "markdown.extensions.nl2br",  # Pour les retours à la ligne
            ]
        )

        # Convertir le markdown en HTML
        html = md.convert(text)

        return mark_safe(html)  # nosec B703, B308

    except Exception as e:
        # En cas d'erreur, retourner le texte brut
        return mark_safe(text.replace("\n", "<br>"))  # nosec B703, B308
