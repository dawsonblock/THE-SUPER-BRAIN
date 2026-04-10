"""Root conftest — ensure brain-ai-rest-service is importable from the repo root."""
import sys
from pathlib import Path

_service_root = Path(__file__).resolve().parent / "brain-ai-rest-service"
if str(_service_root) not in sys.path:
    sys.path.insert(0, str(_service_root))
