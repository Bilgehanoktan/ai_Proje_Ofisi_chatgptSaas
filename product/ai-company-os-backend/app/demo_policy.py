"""Pure synthetic projection, NOT enforcement or authorization."""
from typing import Final
BLOCKED: Final = ("CODE", "REPO", "DEV", "REAL_TEST", "PROD", "SPEND", "EXTERNAL_MUTATION")
def authority_projection() -> dict:
    return {"mode": "D0_SAMPLE_NO_RUNTIME", "effective": False, "security_acceptance": "HOLD", "blocked": list(BLOCKED), "real_test": "NOT_RUN", "enforcement": "NOT_IMPLEMENTED"}
