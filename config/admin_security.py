from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.cache import patch_cache_control
from django_otp import devices_for_user

class StaffAuthMiddleware:
    """Keep administrator enrollment and recovery separate from player login."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path_info.startswith('/staff-auth/'):
            return self.get_response(request)
        login_url = reverse('two_factor:login')
        if request.user.is_authenticated and not (request.user.is_active and request.user.is_staff):
            response = HttpResponseForbidden('Esta sección es solo para administradores.')
        elif request.path_info != login_url and not request.user.is_authenticated:
            response = redirect_to_login(request.path_info, login_url=login_url)
        elif request.path_info != login_url and not request.user.is_verified() and any(devices_for_user(request.user, confirmed=True)):
            response = redirect_to_login(request.path_info, login_url=login_url)
        elif request.path_info != login_url and not request.user.is_verified() and request.path_info not in (reverse('two_factor:setup'),reverse('two_factor:qr')):
            response = redirect('two_factor:setup')
        else:
            response = self.get_response(request)
        patch_cache_control(response, private=True, no_store=True, no_cache=True, max_age=0)
        return response
