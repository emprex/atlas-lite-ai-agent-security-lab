from dataclasses import dataclass
from .config import DATA, settings
from .approval import create, consume
from .audit import emit
from .lifecycle import status as lifecycle_status

SIDE_EFFECTS={"send_email","write_customer_note","execute_refund"}
@dataclass
class Decision:
    allowed: bool
    reason: str
    approval_id: str|None=None

def authorize(tool,args,approval_id=None):
    if tool in SIDE_EFFECTS and (DATA/"KILL_SWITCH").exists():
        emit("policy.denied",tool=tool,args=args,reason="kill_switch"); return Decision(False,"Kill switch active")
    if not settings.guarded:
        emit("policy.allowed",tool=tool,args=args,reason="unsafe_mode"); return Decision(True,"Unsafe mode")
    if tool not in SIDE_EFFECTS:
        emit("policy.denied",tool=tool,args=args,reason="not_allowlisted"); return Decision(False,"Tool not allowlisted")
    lifecycle=lifecycle_status()
    if lifecycle["reassessment_required"]:
        emit("policy.denied",tool=tool,args=args,reason="security_reassessment_required",changed_files=lifecycle["changed_files"])
        return Decision(False,"Security reassessment required")
    if tool=="execute_refund":
        try:
            canonical={"customer_id":int(args["customer_id"]),"amount":round(float(args["amount"]),2),"reason":str(args["reason"])}
        except Exception:
            return Decision(False,"Invalid arguments")
        require=settings.require_approval_all_refunds or canonical["amount"]>settings.approval_threshold
        if require and approval_id:
            ok,reason=consume(approval_id,tool,canonical)
            if ok:
                emit("policy.allowed",tool=tool,args=canonical,reason="exact_action_approval"); return Decision(True,"Exact-action approval valid",approval_id)
            emit("policy.denied",tool=tool,args=canonical,reason=reason,approval_id=approval_id); return Decision(False,f"Approval rejected: {reason}")
        if require:
            rec=create(tool,canonical)
            emit("policy.paused",tool=tool,args=canonical,reason="human_approval_required",approval_id=rec["id"])
            return Decision(False,"Human approval required",rec["id"])
    emit("policy.allowed",tool=tool,args=args,reason="guarded_policy_pass"); return Decision(True,"Policy passed")
