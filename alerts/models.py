from django.db import models
from django.utils import timezone
from core.utils import compute_fingerprint


class AlertStatus(models.TextChoices):
    FIRING = "firing", "Firing"
    RESOLVED = "resolved", "Resolved"
    ACKED = "acked", "Acknowledged"


class Severity(models.TextChoices):
    CRITICAL = "critical", "Critical"
    HIGH = "high", "High"
    WARNING = "warning", "Warning"
    INFO = "info", "Info"
    OK = "ok", "OK"


class AlertGroup(models.Model):
    fingerprint = models.CharField(max_length=128, unique=True, db_index=True)
    status = models.CharField(max_length=16, choices=AlertStatus.choices, default=AlertStatus.FIRING)
    count = models.PositiveIntegerField(default=0)
    first_seen = models.DateTimeField(default=timezone.now)
    last_seen = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "alert_group"

    def __str__(self) -> str:
        return f"Group<{self.fingerprint[:8]}> {self.status} x{self.count}"


class AlertEvent(models.Model):
    source = models.CharField(max_length=32, db_index=True)
    external_id = models.CharField(max_length=128, blank=True, null=True)
    status = models.CharField(max_length=16, choices=AlertStatus.choices, default=AlertStatus.FIRING)
    severity = models.CharField(max_length=16, choices=Severity.choices, default=Severity.WARNING)

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")

    labels = models.JSONField(default=dict, blank=True)
    annotations = models.JSONField(default=dict, blank=True)

    fingerprint = models.CharField(max_length=128, db_index=True)

    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)

    resource = models.CharField(max_length=128, blank=True, default="")  # host/pod/etc.
    service = models.CharField(max_length=128, blank=True, default="")
    metric = models.CharField(max_length=128, blank=True, default="")
    namespace = models.CharField(max_length=128, blank=True, default="")
    generator_url = models.URLField(blank=True, default="")

    group = models.ForeignKey(AlertGroup, on_delete=models.CASCADE, related_name="events", null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "alert_event"
        indexes = [
            models.Index(fields=["fingerprint", "status"]),
            models.Index(fields=["source", "created_at"]),
        ]

    def save(self, *args, **kwargs):
        if not self.fingerprint:
            self.fingerprint = compute_fingerprint(
                source=self.source, labels=self.labels or {}, metric=self.metric or None, title=self.title
            )
        super().save(*args, **kwargs)

