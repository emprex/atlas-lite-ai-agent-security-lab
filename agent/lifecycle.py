from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from .config import DATA, ROOT
from .audit import emit

STATE = DATA / "security-baseline.json"
HISTORY = DATA / "security-lifecycle.jsonl"

MATERIAL_FILES = (
    "agent/policy.py",
    "agent/approval.py",
    "agent/monitoring.py",
    "agent/lifecycle.py",
    "agent/audit.py",
    "agent/engine.py",
    "agent/actions.py",
    "agent/config.py",
    "arl-agent-profile.json",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def current_snapshot() -> dict[str, str | None]:
    return {rel: _sha256(ROOT / rel) for rel in MATERIAL_FILES}


def _append_history(record: dict) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


def load_baseline() -> dict | None:
    if not STATE.exists():
        return None
    try:
        value = json.loads(STATE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return value if isinstance(value, dict) else None


def record_reassessment(evidence_ref: str) -> dict:
    evidence_ref = str(evidence_ref).strip()
    if not evidence_ref:
        raise ValueError("evidence_ref is required")
    rec = {
        "recorded_at": _now(),
        "evidence_ref": evidence_ref,
        "material_files": list(MATERIAL_FILES),
        "snapshot": current_snapshot(),
    }
    DATA.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    history = {
        "event": "lifecycle.reassessment_recorded",
        "ts": rec["recorded_at"],
        "evidence_ref": evidence_ref,
        "material_file_count": len(MATERIAL_FILES),
    }
    _append_history(history)
    emit("lifecycle.reassessment_recorded", evidence_ref=evidence_ref, material_file_count=len(MATERIAL_FILES))
    return status()


def status() -> dict:
    baseline = load_baseline()
    current = current_snapshot()
    if baseline is None:
        return {
            "reassessment_required": True,
            "reason": "no_security_baseline",
            "changed_files": list(MATERIAL_FILES),
            "baseline_recorded_at": None,
            "evidence_ref": None,
        }

    previous = baseline.get("snapshot") if isinstance(baseline.get("snapshot"), dict) else {}
    changed = [rel for rel in MATERIAL_FILES if previous.get(rel) != current.get(rel)]
    result = {
        "reassessment_required": bool(changed),
        "reason": "material_change_detected" if changed else "security_baseline_current",
        "changed_files": changed,
        "baseline_recorded_at": baseline.get("recorded_at"),
        "evidence_ref": baseline.get("evidence_ref"),
    }
    return result


def enforce() -> dict:
    result = status()
    if result["reassessment_required"]:
        emit(
            "lifecycle.security_review_required",
            reason=result["reason"],
            changed_files=result["changed_files"],
            evidence_ref=result.get("evidence_ref"),
        )
        _append_history({
            "event": "lifecycle.security_review_required",
            "ts": _now(),
            "reason": result["reason"],
            "changed_files": result["changed_files"],
            "evidence_ref": result.get("evidence_ref"),
        })
    return result
