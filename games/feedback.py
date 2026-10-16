"""Save anonymous feedback first, then notify the support inbox."""
import json
import logging
from django.conf import settings
from django.core.mail import get_connection, send_mail
from hashlib import sha256
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .i18n import current_language
from .models import UserFeedback


logger = logging.getLogger(__name__)


def notify_support(item):
    category = "Error reportado" if item.category == "bug" else "Sugerencia"
    body = (
        f"{category} #{item.pk}\n"
        f"Sección: {item.page}\nIdioma: {item.language}\n"
        f"Fecha: {item.created_at.isoformat()}\n\n{item.message}\n\n"
        "Una copia permanece guardada en User feedback dentro del administrador de Gchess."
    )
    try:
        # A slow SMTP server must not leave the feedback form waiting indefinitely.
        connection = get_connection(timeout=min(settings.EMAIL_TIMEOUT, 5))
        sent = send_mail(
            f"[Gchess] {category} #{item.pk}", body,
            settings.DEFAULT_FROM_EMAIL, [settings.FEEDBACK_EMAIL],
            connection=connection, fail_silently=False,
        )
        if not sent:
            logger.warning("Feedback %s saved; email backend sent no notification", item.pk)
    except Exception as error:
        # Keep reports usable even when SMTP is unavailable. Never log their contents.
        logger.warning("Feedback %s saved; email notification failed (%s)", item.pk, type(error).__name__)


@require_POST
def submit(request):
    if len(request.body) > 12000:
        return JsonResponse({'error': 'invalid'}, status=400)
    try:
        payload = json.loads(request.body)
        if not isinstance(payload, dict):
            raise ValueError
        message = payload.get('message', '')
        category = payload.get('category')
        page = payload.get('page', '')
        if not isinstance(message, str) or not 5 <= len(message.strip()) <= 2000 or category not in ('idea', 'bug') or not isinstance(page, str):
            raise ValueError
    except (ValueError, TypeError, UnicodeDecodeError):
        return JsonResponse({'error': 'invalid'}, status=400)
    # Do not store network identifiers or URLs with private query parameters.
    key = 'feedback:' + sha256(request.META.get('REMOTE_ADDR', '').encode()).hexdigest()
    if not cache.add(key, True, timeout=30):
        return JsonResponse({'error': 'rate_limit'}, status=429)
    section = page.split('?')[0].split('#')[0].strip('/').split('/')[0]
    safe_page = '/' + section[:60] + '/' if section else '/'
    item = UserFeedback.objects.create(category=category, message=message.strip(), page=safe_page, language=current_language(request))
    notify_support(item)
    return JsonResponse({'saved': True})
