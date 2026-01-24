import hashlib
import hmac
from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from application.models.base import get_db
from application.utilities.config import settings
from application.utilities.audit import setup_logger
from application.core.tasks import task_process_paystack_webhook

logger = setup_logger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/paystack")
async def paystack_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"[WEBHOOK] Received Paystack webhook | IP: {ip_address}")

    body = await request.body()

    signature = request.headers.get("x-paystack-signature")
    if not signature:
        logger.warning(f"[WEBHOOK BLOCKED] Missing signature | IP: {ip_address}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing signature")

    expected_signature = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode(),
        body,
        hashlib.sha512
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        logger.warning(f"[WEBHOOK BLOCKED] Invalid signature | IP: {ip_address}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    import json
    try:
        payload = json.loads(body.decode())
    except json.JSONDecodeError:
        logger.error(f"[WEBHOOK ERROR] Invalid JSON | IP: {ip_address}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON")

    event = payload.get("event")
    data = payload.get("data", {})

    logger.info(
        f"[WEBHOOK] Processing event | Event: {event} | "
        f"Ref: {data.get('reference', 'N/A')} | IP: {ip_address}"
    )

    task_process_paystack_webhook.delay(payload)

    logger.info(f"[WEBHOOK] Queued for processing | Event: {event} | Ref: {data.get('reference', 'N/A')}")
    return {"status": "received"}
