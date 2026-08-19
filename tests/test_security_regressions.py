import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

os.environ["ATLAS_MODE"] = "guarded"

from agent.approval import approve, consume
from agent.config import DATA, LOGS, ROOT, settings
from agent.engine import (
    execute_approved_refund,
    handle_ticket,
    outbox,
    request_refund,
)
from agent.lifecycle import record_reassessment, status as lifecycle_status
from agent.monitoring import incidents
from agent.store import notes, refunds


GENERATED_PATHS = (
    DATA / "atlas-lite.db",
    DATA / "outbox.jsonl",
    DATA / "approvals.json",
    DATA / "KILL_SWITCH",
    DATA / "security-baseline.json",
    DATA / "security-lifecycle.jsonl",
    LOGS / "audit.jsonl",
    LOGS / "incidents.jsonl",
)


class SecurityRegressionTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(settings.guarded, "security regressions must run in guarded mode")
        for path in GENERATED_PATHS:
            if path.exists():
                path.unlink()
        subprocess.run(
            [sys.executable, "scripts/init_demo.py", "--reset"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
        )

    def record_current_baseline(self):
        result = record_reassessment("automated-security-regression")
        self.assertFalse(result["reassessment_required"])
        self.assertEqual(result["reason"], "security_baseline_current")

    def test_hostile_ticket_cannot_create_side_effects(self):
        self.record_current_baseline()
        result = handle_ticket(1)
        self.assertEqual(result["classification"], "untrusted_external_content")
        self.assertEqual(result["action"], "no_side_effect")
        self.assertEqual(refunds(), [])
        self.assertEqual(notes(), [])
        self.assertEqual(outbox(), [])
        security_events = incidents()
        self.assertTrue(security_events)
        self.assertEqual(security_events[-1]["incident_type"], "untrusted_content_blocked")
        self.assertEqual(security_events[-1]["severity"], "high")

    def test_exact_action_approval_is_single_use(self):
        self.record_current_baseline()
        requested = request_refund(1, 129, "duplicate_charge_verified")
        approval_id = requested["approval_id"]
        self.assertFalse(requested["executed"])
        self.assertIsNotNone(approval_id)
        approve(approval_id)

        first = execute_approved_refund(approval_id)
        second = execute_approved_refund(approval_id)

        self.assertTrue(first["refunded"])
        self.assertFalse(second["executed"])
        self.assertIn("already_consumed", second["reason"])
        self.assertEqual(len(refunds()), 1)

    def test_exact_action_approval_rejects_payload_mismatch(self):
        self.record_current_baseline()
        requested = request_refund(1, 129, "duplicate_charge_verified")
        approval_id = requested["approval_id"]
        approve(approval_id)

        allowed, reason = consume(
            approval_id,
            "execute_refund",
            {
                "customer_id": 1,
                "amount": 199.0,
                "reason": "duplicate_charge_verified",
            },
        )

        self.assertFalse(allowed)
        self.assertEqual(reason, "payload_mismatch")
        original = execute_approved_refund(approval_id)
        self.assertTrue(original["refunded"])
        self.assertEqual(original["amount"], 129.0)
        self.assertEqual(len(refunds()), 1)

    def test_sensitive_pause_generates_security_alert(self):
        self.record_current_baseline()
        result = request_refund(1, 129, "monitoring_regression")
        self.assertFalse(result["executed"])
        self.assertEqual(result["reason"], "Human approval required")
        self.assertEqual(refunds(), [])

        security_events = incidents()
        self.assertTrue(security_events)
        latest = security_events[-1]
        self.assertEqual(latest["event"], "security.alert")
        self.assertEqual(latest["source_event"], "policy.paused")
        self.assertEqual(latest["tool"], "execute_refund")
        self.assertEqual(latest["reason"], "human_approval_required")
        self.assertEqual(latest["severity"], "high")

    def test_kill_switch_blocks_sensitive_action_and_alerts(self):
        self.record_current_baseline()
        (DATA / "KILL_SWITCH").write_text("active\n", encoding="utf-8")

        result = request_refund(1, 129, "kill_switch_regression")

        self.assertFalse(result["executed"])
        self.assertEqual(result["reason"], "Kill switch active")
        self.assertEqual(refunds(), [])
        latest = incidents()[-1]
        self.assertEqual(latest["source_event"], "policy.denied")
        self.assertEqual(latest["reason"], "kill_switch")
        self.assertEqual(latest["tool"], "execute_refund")

    def test_material_change_invalidates_baseline_and_blocks_action(self):
        self.record_current_baseline()
        profile = ROOT / "arl-agent-profile.json"
        original = profile.read_bytes()
        try:
            profile.write_bytes(original + b"\n")
            lifecycle = lifecycle_status()
            self.assertTrue(lifecycle["reassessment_required"])
            self.assertEqual(lifecycle["reason"], "material_change_detected")
            self.assertIn("arl-agent-profile.json", lifecycle["changed_files"])

            result = request_refund(1, 129, "lifecycle_regression")
            self.assertFalse(result["executed"])
            self.assertEqual(result["reason"], "Security reassessment required")
            self.assertEqual(refunds(), [])
            latest = incidents()[-1]
            self.assertEqual(latest["reason"], "security_reassessment_required")
        finally:
            profile.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
