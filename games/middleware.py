from django.db import OperationalError, ProgrammingError
from django.db.models import F
from django.utils import timezone

from .models import DailyVisit


class DailyVisitMiddleware:
    EXCLUDED_PREFIXES = (
        '/admin/',
        '/staff-auth/',
        '/static/',
        '/favicon.ico',
        '/healthz/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if self.should_count_visit(request, response):
            self.count_visit()

        return response

    def should_count_visit(self, request, response):
        if request.method != 'GET':
            return False

        if response.status_code >= 400:
            return False

        path = request.path_info or '/'
        return not any(path.startswith(prefix) for prefix in self.EXCLUDED_PREFIXES)

    def count_visit(self):
        today = timezone.localdate()

        try:
            DailyVisit.objects.update_or_create(
                date=today,
                defaults={'visits': F('visits') + 1},
                create_defaults={'visits': 1},
            )
        except (OperationalError, ProgrammingError):
            pass


class PlayerActivityMiddleware:
    """Record one registered player/day, without storing IPs or visited URLs."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if (response.status_code < 400 and request.user.is_authenticated
                and request.user.is_active and not request.user.is_staff
                and not request.path_info.startswith(DailyVisitMiddleware.EXCLUDED_PREFIXES)):
            from .models import PlayerActivityDay
            from .views import touch_presence
            touch_presence(request.user)
            PlayerActivityDay.objects.get_or_create(user=request.user, date=timezone.localdate())
        return response
