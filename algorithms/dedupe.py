from datetime import timedelta
from typing import Optional

from django.utils import timezone

from alerts.models import AlertEvent


DEFAULT_WINDOW_SECONDS = 60


def should_deduplicate(event: AlertEvent, window_seconds: int = DEFAULT_WINDOW_SECONDS) -> Optional[AlertEvent]:
    """
    Return an existing recent event with the same fingerprint inside the time window
    if we should treat the new event as duplicate; otherwise return None.
    """
    window_start = timezone.now() - timedelta(seconds=window_seconds)
    existing = (
        AlertEvent.objects.filter(fingerprint=event.fingerprint, created_at__gte=window_start)
        .exclude(pk=event.pk)
        .order_by("-created_at")
        .first()
    )
    return existing

