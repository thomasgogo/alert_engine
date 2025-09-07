from django.core.management.base import BaseCommand
from rules.models import Rule


class Command(BaseCommand):
    help = "Seed default rules for the alert engine"

    def handle(self, *args, **options):
        Rule.objects.get_or_create(
            name="Critical/High -> email console",
            defaults={
                "enabled": True,
                "order": 1,
                "conditions": [
                    {"path": "severity", "op": "in", "value": ["critical", "high"]},
                ],
                "actions": [
                    {"type": "email", "to": ["oncall@example.com"], "subject": "[{{ severity }}] {{ title }}"}
                ],
            },
        )
        self.stdout.write(self.style.SUCCESS("Seeded default rules (idempotent)"))

