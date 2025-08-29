from .deprecation import get_deprecation


def deprecation_banner(request):  # pragma: no cover (simple context logic)
    """Inject deprecation info if current resolved template is registered.

    We rely on request.resolver_match + template_name hints. For simplicity we
    check common attribute set by TemplateResponse (if available) else fall back
    to path heuristics.
    """
    template_name = getattr(getattr(request, 'resolver_match', None), 'url_name', '')
    # We cannot reliably know final template file here unless views set it, so
    # for our current target we special-case the known path used by the view.
    # Future improvement: custom middleware capturing the actual template render.
    probable_templates = []
    if request.path.endswith('/consultations-distance/'):
        probable_templates.append('chat/consultations_distance.html')

    info = None
    for name in probable_templates:
        dep = get_deprecation(name)
        if dep:
            info = dep
            break

    return {
        'deprecation_info': info
    }
