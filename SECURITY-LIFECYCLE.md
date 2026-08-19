# Atlas Lite security lifecycle gate

Atlas Lite treats changes to security-relevant authority, approval, monitoring, execution, configuration and agent-profile files as material changes.

## Material files

The executable gate tracks:

- `agent/policy.py`
- `agent/approval.py`
- `agent/monitoring.py`
- `agent/engine.py`
- `agent/actions.py`
- `agent/config.py`
- `arl-agent-profile.json`

A baseline stores a SHA-256 digest for each tracked file. If any digest changes, appears or disappears, the prior security baseline is stale.

## Required flow

1. Complete the relevant security assessment/retest for the current version.
2. Record the reviewed evidence reference with `lifecycle record <evidence_ref>`.
3. Before guarded side effects, Atlas compares the current material-file snapshot with that recorded baseline.
4. A material difference causes `security_reassessment_required` and guarded side effects are denied.
5. The changed version must be reassessed/retested before a new evidence reference is recorded.

`lifecycle record` is an explicit local operator action. It records what evidence reference the operator relied on; it is not independent verification and does not itself prove that the referenced assessment or retest was adequate.

## Commands

- `lifecycle status` — read-only comparison with the last security baseline.
- `lifecycle check` — compare and write a lifecycle security-review-required event when stale.
- `lifecycle record <evidence_ref>` — record the current material snapshot after the operator has completed the relevant review/retest.

The lifecycle state is local demo state and is intentionally not committed to the repository.
