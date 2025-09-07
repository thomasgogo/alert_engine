from typing import Optional

from alerts.models import AlertEvent


def simple_root_cause(event: AlertEvent) -> Optional[str]:
    """
    Very basic root cause guess: use service/namespace labels to hint.
    This is a placeholder for a more advanced algorithm.
    """
    if event.service and event.namespace:
        return f"Likely issue within service={event.service} namespace={event.namespace}"
    if event.resource:
        return f"Host/Instance related: {event.resource}"
    return None

