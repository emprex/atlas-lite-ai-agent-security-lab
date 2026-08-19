from datetime import datetime, timezone
import json
from .config import DATA
from .store import connect
from .audit import emit

def send_email(to, subject, body):
    rec={"ts":datetime.now(timezone.utc).isoformat(),"to":to,"subject":subject,"body":body,"simulated":True}
    with (DATA/"outbox.jsonl").open("a",encoding="utf-8") as f: f.write(json.dumps(rec)+"\n")
    emit("tool.executed", tool="send_email", to=to, subject=subject); return rec

def write_customer_note(customer_id, note):
    with connect() as con:
        con.execute("insert into notes(customer_id,note,created_at) values(?,?,?)",(customer_id,note,datetime.now(timezone.utc).isoformat())); con.commit()
    emit("tool.executed", tool="write_customer_note", customer_id=customer_id, note=note); return {"written":True}

def execute_refund(customer_id, amount, reason):
    amount=round(float(amount),2)
    if amount<=0 or amount>500: raise ValueError("Refund amount must be between 0 and 500")
    with connect() as con:
        if not con.execute("select id from customers where id=?",(customer_id,)).fetchone(): raise ValueError("Unknown customer")
        con.execute("insert into refunds(customer_id,amount,reason,created_at) values(?,?,?,?)",(customer_id,amount,reason,datetime.now(timezone.utc).isoformat())); con.commit()
    emit("tool.executed", tool="execute_refund", customer_id=customer_id, amount=amount, reason=reason)
    return {"refunded":True,"amount":amount,"simulated":True}
