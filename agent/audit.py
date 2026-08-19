from datetime import datetime, timezone
import json
from .config import LOGS
AUDIT = LOGS / "audit.jsonl"
def emit(event, **fields):
    LOGS.mkdir(parents=True, exist_ok=True)
    rec = {"ts": datetime.now(timezone.utc).isoformat(), "event": event, **fields}
    with AUDIT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec
