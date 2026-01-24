import asyncio

from celery import shared_task

from application.models import SessionLocal
from application.models.ledger import ExchangeRate
from application.services import email_service as e
from application.services.er_cnvrt_service import ExchangeRateConverter as erc
from application.utilities.audit import setup_logger
from application.utilities.config import settings
from application.utilities.exceptions import ExchangeRateError

BASE = settings.BASE_CURRENCY
QUOTE = settings.QUOTE_CURRENCY

logger = setup_logger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def task_send_verification_email(self, email: str, token: str):
    logger.info(f"[EMAIL TASK] Sending verification email to {email} | Attempt {self.request.retries + 1}/3")
    try:
        e.EmailService.send_verification_email(email, token)
        logger.info(f"[EMAIL SUCCESS] Verification email delivered to {email}")
    except Exception as exc:
        logger.error(f"[EMAIL FAILED] Could not send verification to {email} | Error: {exc} | Will retry...")
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=5,
    default_retry_delay=30,
    autoretry_for=(Exception,)
)
def task_process_paystack_webhook(self, event_data: dict):
    from sqlalchemy import select
    from application.models.base import SessionLocal
    from application.services.ledger_service import LedgerService
    from application.services.registration_service import RegistrationService
    from application.utilities import exceptions as es
    import uuid as uuid_lib

    event_type = event_data.get("event")
    data = event_data.get("data", {})
    reference = data.get("reference", "unknown")
    amount = data.get("amount", 0) / 100 if data.get("amount") else 0
    customer_email = data.get("customer", {}).get("email", "unknown")
    metadata = data.get("metadata", {})

    logger.info(
        f"[WEBHOOK PROCESSING] Event: {event_type} | Ref: {reference} | "
        f"Amount: ₦{amount:,.2f} | Customer: {customer_email} | Attempt {self.request.retries + 1}/5"
    )

    db = SessionLocal()
    try:
        if event_type == "charge.success":
            paystack_ref = data.get("id")
            
            is_tier_payment = reference.startswith("tier_") or metadata.get("payment_type") == "tier_upgrade"
            
            if is_tier_payment:
                tier = metadata.get("tier") or reference.split("_")[1]
                user_id_str = metadata.get("user_id")
                
                if not user_id_str and "_" in reference:
                    parts = reference.split("_")
                    if len(parts) >= 3:
                        user_id_str = parts[2]
                
                logger.info(f"[TIER UPGRADE] Processing tier upgrade | Tier: {tier} | Ref: {reference}")
                
                from application.models.ledger import LedgerTransaction
                from application.models.enums import TransactionStatus
                tx_result = db.execute(
                    select(LedgerTransaction).filter(LedgerTransaction.reference_id == reference)
                )
                transaction = tx_result.scalar_one_or_none()
                
                if transaction:
                    if transaction.status == TransactionStatus.SUCCESS:
                        logger.warning(f"[TIER UPGRADE] Transaction {reference} already processed")
                    else:
                        transaction.status = TransactionStatus.SUCCESS
                        transaction.external_reference = str(paystack_ref)
                        logger.info(f"[TIER UPGRADE] Marked transaction {reference} as SUCCESS")
                
                if user_id_str:
                    try:
                        user_id = uuid_lib.UUID(user_id_str) if len(user_id_str) == 32 else None
                        
                        if user_id is None:
                            from application.models.account import User
                            result = db.execute(select(User).filter(User.email == customer_email))
                            user = result.scalar_one_or_none()
                            user_id = user.id if user else None
                        
                        if user_id and tier in ["plus", "business"]:
                            if tier == "plus":
                                RegistrationService.upgrade_to_plus_sync(db, user_id, reference)
                            elif tier == "business":
                                RegistrationService.upgrade_to_business_sync(db, user_id, reference)
                            
                            logger.info(f"[TIER UPGRADE SUCCESS] User {user_id} upgraded to {tier} | Ref: {reference}")
                        
                    except Exception as upgrade_err:
                        logger.error(f"[TIER UPGRADE ERROR] Failed to upgrade user | Error: {upgrade_err}")
                
                db.commit()
                
            else:
                logger.info(f"[DEPOSIT PROCESSING] Processing successful charge | Ref: {reference} | Paystack ID: {paystack_ref}")
                
                transaction, credited_amount = LedgerService.process_successful_deposit_sync(
                    db, reference, str(paystack_ref)
                )
                db.commit()

                logger.info(
                    f"[DEPOSIT COMPLETED] ₦{credited_amount:,.2f} credited | Ref: {reference} | "
                    f"Customer: {customer_email}"
                )

        elif event_type == "charge.failed":
            failure_reason = data.get("gateway_response", "Unknown error")
            logger.warning(f"[PAYMENT FAILED] Charge failed | Ref: {reference} | Reason: {failure_reason}")

            LedgerService.process_failed_deposit_sync(db, reference, failure_reason)
            db.commit()

            logger.info(f"[PAYMENT MARKED FAILED] Ref: {reference} | Reason: {failure_reason}")

        elif event_type in ["transfer.success", "transfer.failed"]:
            transfer_status = "completed" if event_type == "transfer.success" else "failed"
            logger.info(f"[TRANSFER EVENT] Transfer {transfer_status} | Ref: {reference} | Amount: ₦{amount:,.2f}")

        else:
            logger.info(f"[WEBHOOK IGNORED] Unhandled event type: {event_type} | Ref: {reference}")

    except es.TransactionNotFoundError:
        logger.warning(f"[WEBHOOK SKIP] Transaction not in our system | Ref: {reference} - May be from another account")
    except es.InvalidTransactionStateError as err:
        logger.warning(f"[WEBHOOK DUPLICATE] Transaction already processed | Ref: {reference} | State: {err}")
    except es.SystemAccountNotFoundError as err:
        logger.error(f"[CRITICAL CONFIG ERROR] System account missing | Ref: {reference} | Error: {err} - Create system accounts via admin API")
        raise self.retry(exc=err)
    except es.AccountNotFoundError as err:
        logger.error(f"[USER WALLET MISSING] Cannot credit user | Ref: {reference} | Error: {err}")
        raise self.retry(exc=err)
    except Exception as exc:
        db.rollback()
        logger.error(f"[WEBHOOK ERROR] Processing failed | Ref: {reference} | Error: {exc} | Will retry...")
        raise self.retry(exc=exc)
    finally:
        db.close()


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def task_send_password_reset_email(self, email: str, token: str):
    logger.info(f"[EMAIL TASK] Sending password reset email to {email} | Attempt {self.request.retries + 1}/3")
    try:
        e.EmailService.send_password_reset_email(email, token)
        logger.info(f"[EMAIL SUCCESS] Password reset email delivered to {email}")
    except Exception as exc:
        logger.error(f"[EMAIL FAILED] Could not send password reset to {email} | Error: {exc} | Will retry...")
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def task_send_trade_notification(self, email: str, trade_data: dict):
    trade_id = trade_data.get("id", "unknown")
    symbol = trade_data.get("symbol", "unknown")

    logger.info(f"[EMAIL TASK] Sending trade notification to {email} | Trade: {trade_id} | Symbol: {symbol}")
    try:
        e.EmailService.send_trade_notification(email, trade_data)
        logger.info(f"[EMAIL SUCCESS] Trade notification delivered to {email} | Trade: {trade_id}")
    except Exception as exc:
        logger.error(f"[EMAIL FAILED] Could not send trade notification to {email} | Error: {exc}")
        raise self.retry(exc=exc)
        raise self.retry(exc=exc)

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def task_send_welcome_email(self, email: str, first_name: str):
    try:
        logger.info(f"Sending welcome email to {email}")
        e.EmailService.send_welcome_email(email, first_name)
        logger.info(f"Welcome email sent successfully to {email}")
    except Exception as exc:
        logger.error(f"Failed to send welcome email: {exc}")
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300
)
def task_fetch_and_store_rate(self, base: str = None, quote: str = None):
    base = base or BASE
    quote = quote or QUOTE
    
    logger.info(f"[RATE UPDATE] Starting hourly update for {base}/{quote}")

    db = SessionLocal()

    try:
        rate = asyncio.run(erc.fetch_rate_from_api(base, quote))

        if rate == 0:
            raise ExchangeRateError("Rate returned as 0 (API failure)")
            
        new_rate = ExchangeRate(
            currency_pair=f"{base}-{quote}",
            rate=rate,
            source="openexchangerates.org"
        )

        db.add(new_rate)
        db.commit()
        db.refresh(new_rate)

        logger.info(f"[RATE UPDATE SUCCESS] {base}/{quote} = {rate} (ID: {new_rate.id})")
        return {"rate": str(rate), "id": new_rate.id}

    except Exception as exc:
        logger.error(f"[RATE UPDATE FAILED] {base}/{quote} | Error: {exc}")
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()


