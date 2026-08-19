# Atlas Lite — AI Agent Security Lab

Atlas Lite is a lightweight local AI-agent security lab built to demonstrate how untrusted content can cross an agent trust boundary and trigger privileged actions.

It is designed as a reproducible test target for AI-agent security assessment, remediation and retesting.

Unlike a chatbot demo, Atlas Lite has agent-like authority over local tools and state:

- reads customer support tickets;
- reads local customer records;
- writes CRM-style notes;
- sends simulated outbound email;
- executes simulated refunds;
- records policy and runtime evidence;
- supports exact-action human approval;
- supports a kill switch and deterministic retesting.

All effects are local and simulated. No real payment processor, email provider, production CRM, cloud account or external API is used.

## Why I built it

AI-agent security becomes materially different from ordinary chatbot security when agent decisions can become business actions.

The important question is not only:

> Can the agent produce a bad answer?

It is:

> Can untrusted input cause the agent to misuse its authority, and what evidence proves whether the control worked?

Atlas Lite creates a small, reproducible environment for answering that question.

## Security scenario

The seeded hostile ticket contains text pretending to be an internal finance authorization.

In the deliberately unsafe baseline, Atlas Lite trusts those embedded instructions and performs three simulated side effects:

```text
Untrusted customer ticket
        ↓
Trusted as instructions
        ↓
£129 simulated refund
CRM note written
Outbound email sent
```

This produces test-generated evidence rather than merely describing a theoretical weakness.

A malicious message by itself is not treated as a finding. The relevant evidence is the reproduced unsafe action.

## Guarded version

The same agent can then be run in guarded mode:

```text
Untrusted customer ticket
        ↓
Classified as external untrusted content
        ↓
No privileged side effect
        ↓
Independent human approval where required
        ↓
Exact-action, expiring, one-time authorization
```

This allows the same scenario to be remediated and retested without changing the test target.

## Evidence model

Atlas Lite is designed around a simple evidence chain:

```text
Declared Controls
        ↓
Observed Controls
        ↓
Findings
        ↓
Test Evidence
        ↓
Human Approval
        ↓
Remediation
        ↓
Retest
        ↓
Deployment Decision
```

The repository deliberately separates declarations from proof.

`arl-agent-profile.json` describes the intended architecture, but code inspection and runtime evidence are required to establish what actually happened.

## Architecture

Atlas Lite uses:

- Python;
- SQLite;
- local files;
- deterministic rule-based decision logic;
- no large language model;
- no GPU;
- no cloud dependency.

The deterministic design makes security tests reproducible and keeps the lab suitable for low-resource machines.

### Security-relevant surfaces

**Access**
- local support inbox;
- local knowledge base;
- SQLite customer records;
- runtime evidence files.

**Data**
- synthetic customer PII;
- untrusted external support text;
- persistent CRM notes.

**Actions**
- simulated refund;
- CRM note write;
- simulated outbound email.

**Approval**
- exact action and argument binding;
- expiry;
- one-time consumption.

**Recovery**
- kill switch;
- resettable demo state;
- audit trail.

## Quick start

```bash
git clone https://github.com/emprex/atlas-lite-ai-agent-security-lab.git
cd atlas-lite-ai-agent-security-lab

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
python scripts/init_demo.py --reset
cp .env.example .env
```

Run the unsafe baseline:

```bash
ATLAS_MODE=unsafe python -m agent.cli
```

Then:

```text
list tickets
open ticket 2
handle ticket 2

open ticket 1
handle ticket 1

show refunds
show notes
show outbox
status
```

## Remediation and retest

Reset the lab:

```bash
python scripts/init_demo.py --reset
```

Start guarded mode:

```bash
ATLAS_MODE=guarded python -m agent.cli
```

Replay the same hostile ticket:

```text
open ticket 1
handle ticket 1
show refunds
show notes
show outbox
```

The external ticket should no longer be sufficient to authorize privileged actions.

## Exact-action approval

In guarded mode:

```text
request refund 1 129 duplicate_charge_verified
```

Atlas returns an approval ID.

Approve it from another terminal:

```bash
source .venv/bin/activate
python scripts/approve.py <approval_id>
```

Then execute:

```text
execute approved refund <approval_id>
```

The approval is:

- tied to the specific action;
- tied to the exact customer, amount and reason;
- time limited;
- one-time use.

A replay should be rejected.

## Kill switch

Enable:

```bash
touch data/KILL_SWITCH
```

Disable:

```bash
rm data/KILL_SWITCH
```

Side-effecting actions are denied while the kill switch is active.

## Repository guide

- `agent/engine.py` — unsafe and guarded execution paths
- `agent/policy.py` — authorization policy
- `agent/actions.py` — simulated side-effect tools
- `agent/approval.py` — exact-action approval
- `agent/audit.py` — runtime evidence
- `data/inbox/0001.txt` — hostile test input
- `data/inbox/0002.txt` — benign control case
- `arl-agent-profile.json` — declared architecture
- `ARL-TEST-PLAN.md` — security assessment and retest sequence

## What this project demonstrates

This project demonstrates practical work across:

- AI-agent security;
- trust-boundary design;
- prompt-injection impact testing;
- tool authorization;
- human-in-the-loop approval;
- deterministic security testing;
- audit evidence;
- remediation and retesting;
- deployment decision support.

## Scope and limitations

Atlas Lite is intentionally a security lab, not a production support platform.

It does not claim to prove that an arbitrary AI agent is secure.

It does not use a real LLM in the current version. The deterministic decision layer is intentional so security behavior remains reproducible and suitable for bounded testing.

All customer information is synthetic and all side effects are local simulations.

## Related project

Atlas Lite was created as a test target for AgentRiskLayer, an evidence-first AI-agent security project focused on connecting assessment, observed controls, findings, remediation, retesting and deployment decisions.
