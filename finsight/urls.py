from django.contrib import admin
from django.urls import path, include
from main.views import landing

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', landing, name='landing'),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('core.urls')),
]
