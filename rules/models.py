from django.db import models


class Rule(models.Model):
    name = models.CharField(max_length=128)
    enabled = models.BooleanField(default=True)
    # JSON structure: list of condition dicts
    # e.g. [{"path": "labels.severity", "op": "eq", "value": "critical"}]
    conditions = models.JSONField(default=list, blank=True)
    # actions: list of dicts
    # e.g. [{"type": "email", "to": ["oncall@example.com"], "subject": "{{ title }}"}]
    actions = models.JSONField(default=list, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "rule"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"Rule<{self.name}>"

