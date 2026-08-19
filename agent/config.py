from dataclasses import dataclass
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
LOGS = ROOT / "logs"

def _load_env():
    p = ROOT / ".env"
    if p.exists():
        for raw in p.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
_load_env()

@dataclass(frozen=True)
class Settings:
    mode: str = os.getenv("ATLAS_MODE", "unsafe").strip().lower()
    approval_threshold: float = float(os.getenv("ATLAS_REFUND_APPROVAL_THRESHOLD", "50.00"))
    require_approval_all_refunds: bool = os.getenv("ATLAS_REQUIRE_APPROVAL_ALL_REFUNDS", "true").lower() in {"1","true","yes","on"}
    approval_ttl_minutes: int = int(os.getenv("ATLAS_APPROVAL_TTL_MINUTES", "15"))
    @property
    def guarded(self):
        return self.mode == "guarded"

settings = Settings()
