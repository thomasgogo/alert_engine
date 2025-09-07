import operator
import re
from typing import Any, Dict

from django.template import Template, Context

from alerts.models import AlertEvent
from .models import Rule
from actions.handlers import run_action
from knowledge.services import suggest_articles


OPS = {
    "eq": operator.eq,
    "neq": operator.ne,
    "contains": lambda a, b: (b or "") in (a or ""),
    "regex": lambda a, b: re.search(str(b), str(a) or "") is not None,
    "in": lambda a, b: a in (b or []),
}


def _get_by_path(obj: Dict[str, Any], path: str) -> Any:
    cur: Any = obj
    for p in path.split('.'):
        if isinstance(cur, dict):
            cur = cur.get(p)
        else:
            return None
    return cur


def _render(text: str, context: Dict[str, Any]) -> str:
    return Template(text).render(Context(context))


def _match(rule: Rule, event: AlertEvent) -> bool:
    data = {
        "id": event.id,
        "source": event.source,
        "status": event.status,
        "severity": event.severity,
        "title": event.title,
        "description": event.description,
        "labels": event.labels,
        "annotations": event.annotations,
        "resource": event.resource,
        "service": event.service,
        "metric": event.metric,
        "namespace": event.namespace,
    }
    for cond in rule.conditions or []:
        op = OPS.get(cond.get("op", "eq"))
        path = cond.get("path")
        value = cond.get("value")
        if not op or not path:
            return False
        actual = _get_by_path(data, path)
        if not op(actual, value):
            return False
    return True


def evaluate_rules_on_event(event: AlertEvent) -> None:
    for rule in Rule.objects.filter(enabled=True).order_by('order', 'id'):
        if _match(rule, event):
            kb = suggest_articles(event)
            context = {
                "title": event.title,
                "description": event.description,
                "severity": event.severity,
                "status": event.status,
                "labels": event.labels,
                "annotations": event.annotations,
                "resource": event.resource,
                "service": event.service,
                "metric": event.metric,
                "namespace": event.namespace,
                "generator_url": event.generator_url,
                "kb_articles": [{"title": a.title, "solution": a.solution} for a in kb],
            }
            for action in rule.actions or []:
                # Render template-able fields
                rendered = {k: (_render(v, context) if isinstance(v, str) else v) for k, v in action.items()}
                run_action(rendered, event)

