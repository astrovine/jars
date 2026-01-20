import resend
from typing import Any

from application.utilities.config import settings
from application.utilities.audit import setup_logger
from application.utilities import exceptions as es

logger = setup_logger(__name__)

resend.api_key = settings.RESEND_API_KEY

DEFAULT_FROM_EMAIL = "JARS <noreply@jars.app>"
SECURITY_FROM_EMAIL = "JARS Security <security@jars.app>"

IS_DEVELOPMENT = settings.ENVIRONMENT.lower() in ("development", "dev", "local")


class EmailService:

    @staticmethod
    def send_verification_email(to_email: str, token: str) -> Any:
        link = f"{settings.FRONTEND_URL}/verify?token={token}"

        if IS_DEVELOPMENT:
            logger.info("DEVELOPMENT MODE - EMAIL NOT SENT")
            logger.info(f"To: {to_email}")
            logger.info(f"Subject: Verify your JARS Account")
            logger.info(f"Verification Token: {token}")
            logger.info(f"Verification Link: {link}")
            logger.info(f"API Endpoint: POST /api/v1/auth/verify-email?token={token}")
            return {"id": "dev-mode", "status": "logged"}

        html_content = f"""
        <h1>Welcome to JARS</h1>
        <p>Click the button below to verify your email address:</p>
        <a href="{link}" style="background-color: #4CAF50; color: white; padding: 14px 28px; text-decoration: none; border-radius: 5px;">Verify Email</a>
        <p style="color: #666; font-size: 12px;">This link expires in 24 hours.</p>
        <p style="color: #999; font-size: 11px;">Or copy this link: {link}</p>
        """

        return EmailService._send_email(
            to_email=to_email,
            subject="Verify your JARS Account",
            html_content=html_content,
            from_email=SECURITY_FROM_EMAIL
        )

    @staticmethod
    def send_password_reset_email(to_email: str, token: str) -> Any:
        link = f"{settings.FRONTEND_URL}/reset-password?token={token}"

        if IS_DEVELOPMENT:
            logger.info("DEVELOPMENT MODE - EMAIL NOT SENT")
            logger.info(f"To: {to_email}")
            logger.info(f"Subject: Reset your JARS Password")
            logger.info(f"Reset Token: {token}")
            logger.info(f"Reset Link: {link}")
            logger.info(f"API Endpoint: POST /api/v1/auth/password-reset/confirm")
            return {"id": "dev-mode", "status": "logged"}

        html_content = f"""
        <h1>Password Reset Request</h1>
        <p>Click the button below to set a new password:</p>
        <a href="{link}" style="background-color: #e74c3c; color: white; padding: 14px 28px; text-decoration: none; border-radius: 5px;">Reset Password</a>
        <p style="color: #666; font-size: 12px;">This link expires in 15 minutes.</p>
        """

        return EmailService._send_email(
            to_email=to_email,
            subject="Reset your JARS Password",
            html_content=html_content,
            from_email=SECURITY_FROM_EMAIL
        )

    @staticmethod
    def send_trade_notification(to_email: str, trade_data: dict) -> Any:
        side_color = "#4CAF50" if trade_data.get("side") == "BUY" else "#e74c3c"

        if IS_DEVELOPMENT:
            logger.info("DEVELOPMENT MODE - TRADE NOTIFICATION NOT SENT")
            logger.info(f"To: {to_email}")
            logger.info(f"Trade Data: {trade_data}")
            return {"id": "dev-mode", "status": "logged"}

        html_content = f"""
        <h1>Trade Executed</h1>
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
            <p><strong>Trader:</strong> {trade_data.get("trader_alias", "N/A")}</p>
            <p><strong>Symbol:</strong> {trade_data.get("symbol", "N/A")}</p>
            <p><strong>Side:</strong> <span style="color: {side_color};">{trade_data.get("side", "N/A")}</span></p>
            <p><strong>Quantity:</strong> {trade_data.get("quantity", "N/A")}</p>
            <p><strong>Price:</strong> ${trade_data.get("price", "N/A")}</p>
        </div>
        """

        return EmailService._send_email(
            to_email=to_email,
            subject=f"Trade Executed: {trade_data.get('side', '')} {trade_data.get('symbol', '')}",
            html_content=html_content,
            from_email=DEFAULT_FROM_EMAIL
        )

    @staticmethod
    def _send_email(to_email: str, subject: str, html_content: str, from_email: str = DEFAULT_FROM_EMAIL) -> Any:
        try:
            response = resend.Emails.send({
                "from": from_email,
                "to": to_email,
                "subject": subject,
                "html": html_content
            })
            logger.info(f"Email sent to {to_email}: {subject}")
            return response
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}", exc_info=True)
            raise es.ServiceUnavailableError("Email service")

    @staticmethod
    def send_welcome_email(to_email: str, first_name: str) -> Any:
        dashboard_link = f"{settings.FRONTEND_URL}/dashboard"

        if IS_DEVELOPMENT:
            logger.info("DEVELOPMENT MODE - WELCOME EMAIL NOT SENT")
            logger.info(f"To: {to_email}")
            logger.info(f"Subject: Welcome to JARS, {first_name}!")
            logger.info(f"Dashboard Link: {dashboard_link}")
            return {"id": "dev-mode", "status": "logged"}

        html_content = f"""
        <h1>Welcome to JARS, {first_name}!</h1>
        <p>Your email has been verified and your account is now active.</p>
        <p>You're ready to start copy trading with the best traders in the market.</p>
        <h2>What's Next?</h2>
        <ul>
            <li><strong>Connect your exchange</strong> - Link your Bybit API keys</li>
            <li><strong>Browse traders</strong> - Find top-performing traders to copy</li>
            <li><strong>Start copying</strong> - Automatically replicate trades in real-time</li>
        </ul>
        <a href="{dashboard_link}" style="display: inline-block; background-color: #2ecc71; color: white; padding: 14px 28px; text-decoration: none; border-radius: 5px; margin-top: 20px;">Go to Dashboard</a>
        <p style="color: #666; font-size: 12px; margin-top: 30px;">
            Remember: Never share your API keys with anyone. JARS will never ask for withdrawal permissions.
        </p>
        """

        return EmailService._send_email(
            to_email=to_email,
            subject=f"Welcome to JARS, {first_name}! Your account is ready",
            html_content=html_content,
            from_email=DEFAULT_FROM_EMAIL
        )
