import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def canonical_json(data: Dict[str, Any]) -> str:
    """
    Deterministically serialize dicts for hashing by sorting keys and ensuring
    non-ASCII content is preserved.
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hexdigest(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


from typing import Optional

def compute_fingerprint(*, source: str, labels: Dict[str, Any], metric: Optional[str] = None,
                        title: Optional[str] = None) -> str:
    base = {
        "source": source,
        "metric": metric or "",
        "title": title or "",
        "labels": labels or {},
    }
    return sha256_hexdigest(canonical_json(base))

