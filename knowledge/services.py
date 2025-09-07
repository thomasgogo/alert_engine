import re
from typing import List

from alerts.models import AlertEvent
from .models import KBArticle


def suggest_articles(event: AlertEvent) -> List[KBArticle]:
    candidates = KBArticle.objects.filter(enabled=True)
    data = (event.title or "") + "\n" + str(event.labels or {})
    matched = []
    for a in candidates:
        try:
            if re.search(a.pattern, data):
                matched.append(a)
        except re.error:
            # ignore bad regex
            continue
    return matched

