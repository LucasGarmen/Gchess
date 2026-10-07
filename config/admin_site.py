from django.contrib.auth.views import redirect_to_login
from django.urls import reverse
from two_factor.admin import AdminSiteOTPRequired

class SecureAdminSite(AdminSiteOTPRequired):
    site_header = 'Gchess · Administración'
    site_title = 'Gchess admin'

    def login(self, request, extra_context=None):
        # Always use the MFA login, even when the ordinary site login is available.
        return redirect_to_login(reverse('admin:index'), login_url=reverse('two_factor:login'))
