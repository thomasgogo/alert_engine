from django.contrib import admin
from .models import Rule


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ("name", "enabled", "order")
    list_editable = ("enabled", "order")

