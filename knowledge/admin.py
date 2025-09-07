from django.contrib import admin
from .models import KBArticle


@admin.register(KBArticle)
class KBArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "enabled", "priority")
    list_editable = ("enabled", "priority")

