from django.contrib.auth.views import redirect_to_login
from django.urls import reverse
from two_factor.admin import AdminSiteOTPRequired

class SecureAdminSite(AdminSiteOTPRequired):
    site_header = 'Gchess · Administración'
    site_title = 'Gchess admin'
    index_template = 'admin/gchess_index.html'

    def get_urls(self):
        from django.urls import path
        from games.admin_metrics import dashboard
        return [path('players/activity/',self.admin_view(lambda request: dashboard(self,request)),name='player_activity')] + super().get_urls()

    def login(self, request, extra_context=None):
        # Always use the MFA login, even when the ordinary site login is available.
        return redirect_to_login(reverse('admin:index'), login_url=reverse('two_factor:login'))
