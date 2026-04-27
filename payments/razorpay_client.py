import decimal
import logging
import razorpay
from django.conf import settings

logger = logging.getLogger(__name__)

def _get_client() -> razorpay.Client:
    key_id = getattr(settings, "RAZORPAY_KEY_ID", None)
    key_secret = getattr(settings, "RAZORPAY_KEY_SECRET", None)

    if not key_id or not key_secret:
        logger.error("Razorpay credentials missing in settings")
        raise RuntimeError("Razorpay credentials are not configured.")

    return razorpay.Client(auth=(key_id, key_secret))

def create_order(amount, currency: str = "INR") -> dict:
    """Creates a Razorpay order. Amount is in Rupees."""
    if isinstance(amount, decimal.Decimal):
        amount = float(amount)

    # Razorpay expects amount in paise (multiply by 100)
    amount_paise = int(round(amount * 100))

    client = _get_client()
    return client.order.create({"amount": amount_paise, "currency": currency})

def verify_payment_signature(razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
    """Verifies that the payment signature matches."""
    try:
        client = _get_client()
        return client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        })
    except Exception as e:
        logger.error(f"Signature verification failed: {e}")
        return False