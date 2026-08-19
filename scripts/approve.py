from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from agent.approval import approve
if len(sys.argv)!=2: raise SystemExit("Usage: python scripts/approve.py <approval_id>")
rec=approve(sys.argv[1]); print(f"Approved {rec['id']} for exact action until {rec['expires_at']}")
