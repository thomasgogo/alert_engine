from django.db import models
from alerts.models import AlertGroup, AlertStatus


class Ticket(models.Model):
    group = models.ForeignKey(AlertGroup, on_delete=models.CASCADE, related_name='tickets')
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=16, choices=AlertStatus.choices, default=AlertStatus.FIRING)
    assignee = models.CharField(max_length=128, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ticket'

    def __str__(self) -> str:
        return f"Ticket<{self.id}> {self.title}"

