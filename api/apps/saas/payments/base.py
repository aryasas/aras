# gemini-2-5-flash
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from core import Aras

class Checkout(Aras.Schema):
    id: str
    url: str
    status: str = "pending"

class WebhookEvent(Aras.Schema):
    event_type: str
    payment_id: Optional[str] = None
    status: str
    raw_data: Dict[str, Any]
    subscription_id: Optional[int] = None
    amount: Optional[float] = None
    currency: Optional[str] = None

class PaymentProvider(Aras, ABC):
    code: str       # "stripe" | "midtrans" | "xendit"
    label: str
    countries: List[str]  # ["*"] = global, ["ID"] = country-locked

    @abstractmethod
    def create_checkout(self, subscription: Any, amount: float, currency: str, return_url: str) -> Checkout:
        pass

    @abstractmethod
    def verify_webhook(self, headers: Dict[str, str], raw_body: bytes) -> WebhookEvent:
        pass

    @abstractmethod
    def refund(self, payment_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def list_methods(self, country: Optional[str] = None) -> List[Dict[str, Any]]:
        pass
