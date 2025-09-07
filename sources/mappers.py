from typing import Any, Dict, Iterable, List
from datetime import datetime


def _str(d: Dict[str, Any], key: str, default: str = "") -> str:
    v = d.get(key)
    return "" if v is None else str(v)


def _severity_from_text(text: str) -> str:
    t = (text or "").lower()
    if t in {"critical", "disaster", "fatal"}:
        return "critical"
    if t in {"high"}:
        return "high"
    if t in {"warn", "warning"}:
        return "warning"
    if t in {"info", "information"}:
        return "info"
    return "warning"


def map_alertmanager(payload: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    # https://prometheus.io/docs/alerting/latest/configuration/#webhook_config
    alerts: List[Dict[str, Any]] = payload.get("alerts") or []
    common = payload.get("commonLabels") or {}
    for a in alerts:
        labels = {**common, **(a.get("labels") or {})}
        annotations = a.get("annotations") or {}
        yield {
            "source": "prometheus",
            "external_id": labels.get("alertname"),
            "status": a.get("status", "firing"),
            "severity": labels.get("severity", "warning"),
            "title": labels.get("alertname", "Prometheus Alert"),
            "description": annotations.get("description") or annotations.get("summary") or "",
            "labels": labels,
            "annotations": annotations,
            "starts_at": a.get("startsAt"),
            "ends_at": a.get("endsAt"),
            "resource": labels.get("instance", ""),
            "service": labels.get("job", ""),
            "metric": labels.get("__name__") or labels.get("alertname"),
            "namespace": labels.get("namespace", ""),
            "generator_url": a.get("generatorURL"),
        }


def map_zabbix(payload: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    # Zabbix webhook payloads can vary. This handler tries to map common fields.
    # https://git.zabbix.com/projects/ZBX/repos/zabbix/browse/templates/media/slack
    event_value = _str(payload, "event_value") or _str(payload, "value")
    status = "firing" if event_value in {"1", "problem", "PROBLEM"} else "resolved"
    severity_txt = _str(payload, "severity") or _str(payload, "event_severity") or "warning"
    host = _str(payload, "host") or _str(payload, "host_name")
    title = _str(payload, "subject") or _str(payload, "event_name") or _str(payload, "eventid")
    description = _str(payload, "message") or _str(payload, "event_description")

    labels = {
        "eventid": _str(payload, "eventid"),
        "host": host,
        "severity": severity_txt.lower(),
    }

    yield {
        "source": "zabbix",
        "external_id": _str(payload, "eventid"),
        "status": status,
        "severity": _severity_from_text(severity_txt),
        "title": title or "Zabbix Alert",
        "description": description,
        "labels": labels,
        "annotations": {"raw": payload},
        "starts_at": payload.get("event_time") or payload.get("datetime"),
        "resource": host,
        "service": _str(payload, "trigger_name") or _str(payload, "item_name"),
        "metric": _str(payload, "item_key") or _str(payload, "metric"),
        "generator_url": _str(payload, "event_url") or _str(payload, "trigger_url"),
    }


def map_grafana(payload: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    # Grafana unified alerting webhook
    # https://grafana.com/docs/grafana/latest/alerting/notify/ 
    state = (payload.get("state") or payload.get("status") or "alerting").lower()
    status = "firing" if state in {"alerting", "firing"} else "resolved"
    rule_name = _str(payload, "ruleName") or _str(payload, "title")
    rule_url = _str(payload, "ruleUrl") or _str(payload, "imageUrl")
    message = _str(payload, "message")

    labels = payload.get("labels") or {}
    if not labels:
        # Fall back to tags in evalMatches
        for m in payload.get("evalMatches", []) or []:
            labels.update(m.get("tags") or {})
    severity = labels.get("severity", "warning")

    yield {
        "source": "grafana",
        "external_id": _str(payload, "ruleId") or rule_name,
        "status": status,
        "severity": severity,
        "title": rule_name or "Grafana Alert",
        "description": message,
        "labels": labels,
        "annotations": {"raw": payload},
        "resource": labels.get("instance", ""),
        "service": labels.get("job", ""),
        "namespace": labels.get("namespace", ""),
        "generator_url": rule_url,
    }

