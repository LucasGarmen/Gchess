"""Small, anonymous feedback inbox; never sends email or calls external services."""
import json
from hashlib import sha256
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .i18n import current_language
from .models import UserFeedback


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
    UserFeedback.objects.create(category=category, message=message.strip(), page=safe_page, language=current_language(request))
    return JsonResponse({'saved': True})
