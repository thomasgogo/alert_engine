import logging
from typing import Any, Dict, List

import httpx
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


def _as_list(v: Any) -> List[str]:
    if v is None:
        return []
    if isinstance(v, (list, tuple)):
        return list(v)
    return [str(v)]


def run_action(action: Dict[str, Any], event) -> None:
    """
    action examples:
    - {"type": "email", "to": ["ops@example.com"], "subject": "{{ title }}", "body": "..."}
    - {"type": "webhook", "url": "https://hooks.slack.com/...", "json": {"text": "{{ title }}"}}
    """
    atype = action.get("type")
    if atype == "email":
        to = _as_list(action.get("to"))
        if not to:
            return
        subject = action.get("subject") or f"[{event.severity}] {event.title}"
        body = action.get("body") or (event.description or str(event.labels))
        try:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, to, fail_silently=True)
            logger.info("Sent email to %s for event %s", to, event.id)
        except Exception as e:
            logger.exception("Failed to send email: %s", e)
    elif atype == "webhook":
        url = action.get("url")
        if not url:
            return
        json_payload = action.get("json") or {"title": event.title, "severity": event.severity}
        headers = action.get("headers") or {}
        try:
            httpx.post(url, json=json_payload, headers=headers, timeout=10)
            logger.info("Posted webhook to %s for event %s", url, event.id)
        except Exception as e:
            logger.exception("Failed to post webhook: %s", e)
    else:
        logger.warning("Unknown action type: %s", atype)

