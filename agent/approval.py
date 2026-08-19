from datetime import datetime, timezone, timedelta
import hashlib, json, uuid
from .config import DATA, settings
from .audit import emit
PATH = DATA / "approvals.json"

def _load():
    return json.loads(PATH.read_text(encoding="utf-8") or "{}") if PATH.exists() else {}
def _save(d): PATH.write_text(json.dumps(d, indent=2, sort_keys=True), encoding="utf-8")
def digest(action, args):
    s = json.dumps({"action": action, "args": args}, sort_keys=True, separators=(",",":"))
    return hashlib.sha256(s.encode()).hexdigest()
def create(action, args):
    d=_load(); now=datetime.now(timezone.utc); aid="apr_"+uuid.uuid4().hex[:12]
    rec={"id":aid,"action":action,"args":args,"digest":digest(action,args),
         "created_at":now.isoformat(),"expires_at":(now+timedelta(minutes=settings.approval_ttl_minutes)).isoformat(),
         "approved_at":None,"consumed_at":None}
    d[aid]=rec; _save(d); emit("approval.requested", approval_id=aid, action=action, args=args, digest=rec["digest"]); return rec
def approve(aid):
    d=_load(); rec=d.get(aid)
    if not rec: raise KeyError("Unknown approval ID")
    if rec["consumed_at"]: raise ValueError("Approval already consumed")
    rec["approved_at"]=datetime.now(timezone.utc).isoformat(); d[aid]=rec; _save(d)
    emit("approval.granted", approval_id=aid, digest=rec["digest"]); return rec
def consume(aid, action, args):
    d=_load(); rec=d.get(aid)
    if not rec: return False,"unknown_approval"
    if not rec["approved_at"]: return False,"not_approved"
    if rec["consumed_at"]: return False,"already_consumed"
    if datetime.now(timezone.utc) > datetime.fromisoformat(rec["expires_at"]): return False,"expired"
    if rec["digest"] != digest(action,args): return False,"payload_mismatch"
    rec["consumed_at"]=datetime.now(timezone.utc).isoformat(); d[aid]=rec; _save(d)
    emit("approval.consumed", approval_id=aid, digest=rec["digest"]); return True,"ok"
