import logging
from datetime import datetime
from typing import Any, Dict, Optional

from django.db import transaction
from django.utils.dateparse import parse_datetime

from core.utils import compute_fingerprint, utcnow
from .models import AlertEvent, AlertGroup, AlertStatus

logger = logging.getLogger(__name__)

# Normalized alert payload schema expected by this service:
# {
#   source: 'prometheus'|'zabbix'|'grafana'|'custom',
#   external_id: str|None,
#   status: 'firing'|'resolved',
#   severity: 'critical'|'high'|'warning'|'info'|'ok',
#   title: str,
#   description: str,
#   labels: dict,
#   annotations: dict,
#   starts_at: str|datetime|None,
#   ends_at: str|datetime|None,
#   resource, service, metric, namespace, generator_url
# }

def _parse_dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    # try isoformat string
    dt = parse_datetime(str(value))
    return dt or utcnow()


@transaction.atomic
def ingest_standard_alert(data: Dict[str, Any]) -> AlertEvent:
    labels = data.get("labels") or {}
    fingerprint = compute_fingerprint(
        source=data.get("source", "custom"),
        labels=labels,
        metric=data.get("metric"),
        title=data.get("title"),
    )

    group, created = AlertGroup.objects.select_for_update().get_or_create(
        fingerprint=fingerprint,
        defaults={"status": data.get("status", AlertStatus.FIRING), "count": 0},
    )

    if not created:
        group.last_seen = utcnow()
        group.count = group.count + 1
        # if any event is resolved, let group reflect resolution
        if data.get("status") == AlertStatus.RESOLVED:
            group.status = AlertStatus.RESOLVED
        group.save(update_fields=["last_seen", "count", "status"])
    else:
        group.count = 1
        group.save(update_fields=["count"])

    event = AlertEvent.objects.create(
        source=data.get("source", "custom"),
        external_id=data.get("external_id"),
        status=data.get("status", AlertStatus.FIRING),
        severity=data.get("severity", "warning"),
        title=data.get("title", ""),
        description=data.get("description", ""),
        labels=labels,
        annotations=data.get("annotations") or {},
        fingerprint=fingerprint,
        starts_at=_parse_dt(data.get("starts_at")),
        ends_at=_parse_dt(data.get("ends_at")),
        resource=data.get("resource", ""),
        service=data.get("service", ""),
        metric=data.get("metric", ""),
        namespace=data.get("namespace", ""),
        generator_url=data.get("generator_url", ""),
        group=group,
    )

    logger.info("Ingested event %s in group %s", event.id, group.fingerprint[:8])

    return event

