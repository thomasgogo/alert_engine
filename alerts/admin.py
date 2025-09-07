from django.contrib import admin
from .models import AlertEvent, AlertGroup


@admin.register(AlertGroup)
class AlertGroupAdmin(admin.ModelAdmin):
    list_display = ("fingerprint", "status", "count", "first_seen", "last_seen")
    search_fields = ("fingerprint",)


@admin.register(AlertEvent)
class AlertEventAdmin(admin.ModelAdmin):
    list_display = ("id", "source", "status", "severity", "title", "created_at")
    list_filter = ("source", "status", "severity")
    search_fields = ("title", "resource", "service", "metric", "fingerprint")

