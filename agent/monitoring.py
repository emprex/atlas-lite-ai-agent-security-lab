from datetime import datetime, timezone
import json

from .config import LOGS

INCIDENTS = LOGS / "incidents.jsonl"


def _write_incident(record):
    LOGS.mkdir(parents=True, exist_ok=True)
    with INCIDENTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def observe_audit_event(audit_record):
    """Create a local security incident for bounded high-signal events.

    Raw prompt content and arbitrary tool arguments are intentionally not copied
    into the incident record. The audit log remains the detailed technical trace.
    """
    event = audit_record.get("event")
    tool = audit_record.get("tool")
    reason = audit_record.get("reason")

    incident_type = None
    severity = None

    if event == "policy.denied":
        incident_type = "policy_denied"
        severity = "high" if tool == "execute_refund" else "medium"
    elif event == "policy.paused":
        incident_type = "sensitive_action_paused"
        severity = "high" if tool == "execute_refund" else "medium"
    elif (
        event == "ticket.handling.completed"
        and audit_record.get("classification") == "untrusted_external_content"
        and audit_record.get("action") == "no_side_effect"
    ):
        incident_type = "untrusted_content_blocked"
        severity = "high"

    if not incident_type:
        return None

    incident = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "security.alert",
        "incident_type": incident_type,
        "severity": severity,
        "source_event": event,
        "tool": tool,
        "reason": reason,
        "approval_id": audit_record.get("approval_id"),
    }
    _write_incident(incident)

    detail = tool or incident_type
    suffix = f" reason={reason}" if reason else ""
    print(f"SECURITY ALERT [{severity.upper()}] {detail}{suffix}")
    return incident


def incidents():
    if not INCIDENTS.exists():
        return []
    records = []
    with INCIDENTS.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records
