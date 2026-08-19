import json,shlex
from .config import settings
from .engine import list_tickets,read_ticket,handle_ticket,request_refund,execute_approved_refund,status,outbox
from .store import customer,refunds,notes
from .monitoring import incidents
from .lifecycle import status as lifecycle_status, enforce as lifecycle_check, record_reassessment
HELP="""Commands:
  help
  list tickets
  open ticket <id>
  handle ticket <id>
  show customer <id>
  show refunds
  show notes
  show outbox
  show incidents
  request refund <customer_id> <amount> <reason>
  execute approved refund <approval_id>
  lifecycle status
  lifecycle check
  lifecycle record <evidence_ref>
  status
  quit
"""
def p(x): print(x if isinstance(x,str) else json.dumps(x,indent=2,ensure_ascii=False))
def main():
    print(f"Atlas Lite 1.0 | mode={settings.mode}"); print("Type 'help' for commands.")
    while True:
        try: raw=input("\natlas> ").strip()
        except (EOFError,KeyboardInterrupt): print(); break
        if not raw: continue
        if raw.lower() in {"quit","exit"}: break
        try:
            parts=shlex.split(raw); low=[x.lower() for x in parts]
            if low==["help"]: print(HELP)
            elif low==["list","tickets"]: p(list_tickets())
            elif len(low)==3 and low[:2]==["open","ticket"]: p(read_ticket(int(parts[2])))
            elif len(low)==3 and low[:2]==["handle","ticket"]: p(handle_ticket(int(parts[2])))
            elif len(low)==3 and low[:2]==["show","customer"]: p(customer(int(parts[2])))
            elif low==["show","refunds"]: p(refunds())
            elif low==["show","notes"]: p(notes())
            elif low==["show","outbox"]: p(outbox())
            elif low==["show","incidents"]: p(incidents())
            elif len(parts)>=5 and low[:2]==["request","refund"]: p(request_refund(int(parts[2]),float(parts[3])," ".join(parts[4:])))
            elif len(parts)==4 and low[:3]==["execute","approved","refund"]: p(execute_approved_refund(parts[3]))
            elif low==["lifecycle","status"]: p(lifecycle_status())
            elif low==["lifecycle","check"]: p(lifecycle_check())
            elif len(parts)>=3 and low[:2]==["lifecycle","record"]: p(record_reassessment(" ".join(parts[2:])))
            elif low==["status"]: p(status())
            else: print("Unknown command. Type 'help'.")
        except Exception as e: print(f"ERROR: {type(e).__name__}: {e}")
if __name__=="__main__": main()
