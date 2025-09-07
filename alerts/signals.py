from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import AlertEvent
from rules.engine import evaluate_rules_on_event
from algorithms.dedupe import should_deduplicate


@receiver(post_save, sender=AlertEvent)
def on_event_created(sender, instance: AlertEvent, created: bool, **kwargs):
    if created:
        # Drop noisy duplicates from rule evaluation within a short window
        if should_deduplicate(instance):
            return
        # Evaluate rule engine synchronously for now
        evaluate_rules_on_event(instance)

