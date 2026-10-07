from games.health import health
from django.contrib import admin
from django.urls import path, include
from django.templatetags.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('healthz/', health, name='health'),
    path('favicon.ico', RedirectView.as_view(url=static('images/favicon.png'), permanent=True)),
    path('admin/', admin.site.urls),
    path('staff-auth/', include('config.staff_urls', namespace='two_factor')),
    path('', include('games.urls')),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]
