import json,re
from .config import DATA,settings
from .audit import emit
from . import actions
from .policy import authorize
from .store import customer,refunds,notes

def list_tickets(): return [{"ticket_id":int(p.stem),"file":p.name} for p in sorted((DATA/"inbox").glob("*.txt"))]
def read_ticket(tid):
    p=DATA/"inbox"/f"{tid:04d}.txt"
    if not p.exists(): raise ValueError("Ticket not found")
    return p.read_text(encoding="utf-8")
def outbox():
    p=DATA/"outbox.jsonl"
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []
def _cid(t):
    m=re.search(r"Customer-ID:\s*(\d+)",t,re.I); return int(m.group(1)) if m else None
def _sender(t):
    m=re.search(r"From:\s*([^\s]+)",t,re.I); return m.group(1) if m else "unknown@example.test"
def _subject(t):
    m=re.search(r"Subject:\s*(.+)",t,re.I); return m.group(1).strip() if m else "Support update"

def handle_ticket(tid):
    text=read_ticket(tid); cid=_cid(text); emit("ticket.handling.started",ticket_id=tid,mode=settings.mode)
    if settings.guarded:
        result={"ticket_id":tid,"customer_id":cid,"classification":"untrusted_external_content","action":"no_side_effect",
                "message":"External content is not accepted as authorization. Human review required before refund."}
        emit("ticket.handling.completed",**result); return result
    amount=None
    m=re.search(r"refund\s*[£$]?\s*(\d+(?:\.\d+)?)",text,re.I)
    if m: amount=float(m.group(1))
    note=None
    m=re.search(r'write\s+"([^"]+)"\s+into\s+the\s+CRM\s+notes',text,re.I)
    if m: note=m.group(1)
    performed=[]
    if amount and cid:
        args={"customer_id":cid,"amount":amount,"reason":"instruction extracted from support ticket"}
        if authorize("execute_refund",args).allowed: performed.append(actions.execute_refund(**args))
    if note and cid:
        args={"customer_id":cid,"note":note}
        if authorize("write_customer_note",args).allowed: performed.append(actions.write_customer_note(**args))
    if re.search(r"email me confirming",text,re.I):
        args={"to":_sender(text),"subject":f"Re: {_subject(text)}","body":"Your requested support action has been processed."}
        if authorize("send_email",args).allowed: performed.append(actions.send_email(**args))
    result={"ticket_id":tid,"customer_id":cid,"classification":"external_content_trusted_by_unsafe_parser","performed":performed}
    emit("ticket.handling.completed",ticket_id=tid,performed_count=len(performed),mode=settings.mode); return result

def request_refund(cid,amount,reason):
    args={"customer_id":int(cid),"amount":round(float(amount),2),"reason":str(reason)}
    d=authorize("execute_refund",args)
    return actions.execute_refund(**args) if d.allowed else {"executed":False,"reason":d.reason,"approval_id":d.approval_id,"args":args}

def execute_approved_refund(aid):
    approvals=json.loads((DATA/"approvals.json").read_text(encoding="utf-8") or "{}"); rec=approvals.get(aid)
    if not rec: return {"executed":False,"reason":"unknown approval"}
    d=authorize("execute_refund",rec["args"],approval_id=aid)
    return actions.execute_refund(**rec["args"]) if d.allowed else {"executed":False,"reason":d.reason}

def status():
    return {"mode":settings.mode,"kill_switch":(DATA/"KILL_SWITCH").exists(),"refund_count":len(refunds()),"note_count":len(notes()),"outbox_count":len(outbox())}
