from fastapi import APIRouter
from core.response import ok
import hashlib

# gemini-3-flash-preview
CONSENT_POLICY = {
    "version": "2026.1",
    "text": {
        "en": "I agree to receive marketing communications and process my personal data according to the Privacy Policy.",
        "id": "Saya setuju untuk menerima komunikasi pemasaran dan memproses data pribadi saya sesuai dengan Kebijakan Privasi."
    }
}

# gemini-3-flash-preview
router = APIRouter(prefix="/consent", tags=["Consent"])

# gemini-3-flash-preview
@router.get("/policy")
def get_consent_policy():
    text_en = CONSENT_POLICY["text"]["en"]
    text_hash = hashlib.sha256(text_en.encode()).hexdigest()
    return {
        "version": CONSENT_POLICY["version"],
        "text": CONSENT_POLICY["text"],
        "text_hash": text_hash
    }
