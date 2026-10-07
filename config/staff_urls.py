from django.contrib.admin.forms import AdminAuthenticationForm
from django.urls import path
from two_factor.forms import AuthenticationTokenForm, BackupTokenForm
from two_factor.urls import urlpatterns as original_urls
from two_factor.views import LoginView

class StaffLoginView(LoginView):
    form_list = (('auth', AdminAuthenticationForm), ('token', AuthenticationTokenForm), ('backup', BackupTokenForm))

app_name = 'two_factor'
urlpatterns = [path('account/login/', StaffLoginView.as_view(), name='login')]
urlpatterns += [entry for entry in original_urls[0] if entry.name != 'login']
