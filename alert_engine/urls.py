from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    # Webhook ingestion endpoints
    path('api/v1/webhooks/', include('sources.urls')),
    # Basic alert browsing endpoints (optional)
    path('api/v1/alerts/', include('alerts.urls')),
]
