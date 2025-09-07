from django.apps import AppConfig


class AlertsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'alerts'

    def ready(self) -> None:
        # Import signal handlers
        try:
            import alerts.signals  # noqa: F401
        except Exception:
            pass

