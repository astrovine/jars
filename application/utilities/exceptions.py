"""A bunch of custom exceptions I wrote for the application error handling"""

from fastapi import HTTPException, status

class JARSException(Exception):
    """Base exception for JARS copy trading platform"""
    def __init__(self, detail: str, code: str = "INTERNAL_ERROR"):
        self.detail = detail
        self.code = code
        super().__init__(self.detail)

class InvalidRequestError(JARSException):
    """Raised when the request is invalid or malformed"""
    def __init__(self, detail: str = "Invalid request"):
        super().__init__(detail, "INVALID_REQUEST")


class ResourceNotFoundError(JARSException):
    """Raised when a requested resource is not found"""
    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} not found", "RESOURCE_NOT_FOUND")

class EmailAlreadyExistsError(JARSException):
    """Raised when email already exists"""
    def __init__(self, resource: str = ""):
        super().__init__("Email already exists", "EMAIL_ALREADY_EXISTS")

class AccountAlreadyExistsError(JARSException):
    """Raised when account already exists"""
    def __init__(self, detail: str = "Account already exists"):
        super().__init__(detail, "ACCOUNT_ALREADY_EXISTS")

class DatabaseError(JARSException):
    """Raised when a database operation fails"""
    def __init__(self, reason: str = ""):
        detail = f"Database error: {reason}" if reason else "A database error occurred"
        super().__init__(detail, "DATABASE_ERROR")


class ServiceUnavailableError(JARSException):
    """Raised when an external service is unavailable"""
    def __init__(self, service: str = "External service"):
        super().__init__(f"{service} is unavailable", "SERVICE_UNAVAILABLE")


class ExchangeConnectionError(JARSException):
    """Raised when an exchange connection fails"""
    def __init__(self, exchange: str = "Exchange"):
        super().__init__(f"{exchange} connection failed", "EXCHANGE_CONNECTION_FAILED")

class ExchangeVerificationError(JARSException):
    """Raised when an exchange verification fails"""
    def __init__(self, exchange: str = "Exchange"):
        super().__init__(f"{exchange} verification failed", "EXCHANGE_VERIFICATION_FAILED")

class PermissionDeniedError(JARSException):
    """Raised when user lacks permission for an action"""
    def __init__(self, detail: str = "You do not have permission to perform this action"):
        super().__init__(detail, "PERMISSION_DENIED")

class DuplicateAPIKeyError(JARSException):
    """Raised when API key already exists"""
    def __init__(self, detail: str = "API key already exists"):
        super().__init__(detail, "DUPLICATE_API_KEY")


class RateLimitExceededError(JARSException):
    """Raised when rate limit is exceeded"""
    def __init__(self, detail: str = "Too many requests. Please try again later"):
        super().__init__(detail, "RATE_LIMIT_EXCEEDED")

class AuthenticationError(JARSException):
    """Base class for authentication-related errors"""
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(detail, "AUTHENTICATION_FAILED")


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid"""
    def __init__(self, detail: str = "Invalid email or password"):
        super().__init__(detail)


class TokenExpiredError(AuthenticationError):
    """Raised when access token has expired"""
    def __init__(self):
        super().__init__("Access token has expired")


class InvalidTokenError(AuthenticationError):
    """Raised when token is invalid"""
    def __init__(self, detail: str = "Invalid or malformed token"):
        super().__init__(detail)


class EmailNotVerifiedError(AuthenticationError):
    """Raised when user tries to login without verifying email"""
    def __init__(self, detail: str = "Please verify your email before logging in"):
        super().__init__(detail)


class RefreshTokenExpiredError(AuthenticationError):
    """Raised when refresh token has expired"""
    def __init__(self):
        super().__init__("Refresh token has expired")


class InvalidResetTokenError(JARSException):
    """Raised when password reset token is invalid"""
    def __init__(self, detail: str = "Invalid or expired password reset token"):
        super().__init__(detail, "INVALID_RESET_TOKEN")


class ExpiredResetTokenError(JARSException):
    """Raised when password reset token has expired"""
    def __init__(self, detail: str = "Password reset token has expired"):
        super().__init__(detail, "RESET_TOKEN_EXPIRED")


class PasswordMismatchError(JARSException):
    """Raised when passwords do not match"""
    def __init__(self, detail: str = "Passwords do not match"):
        super().__init__(detail, "PASSWORD_MISMATCH")


class UserNotFoundError(ResourceNotFoundError):
    """Raised when user is not found"""
    def __init__(self, detail: str = "User not found"):
        super().__init__(detail)


class DuplicateEmailError(JARSException):
    """Raised when email already exists"""
    def __init__(self):
        super().__init__("Email already exists", "DUPLICATE_EMAIL")


class UserCreationError(JARSException):
    """Raised when user creation fails"""
    def __init__(self, detail: str = "Failed to create user"):
        super().__init__(detail, "USER_CREATION_ERROR")


class UserUpdateError(JARSException):
    """Raised when user update fails"""
    def __init__(self, detail: str = "Failed to update user"):
        super().__init__(detail, "USER_UPDATE_ERROR")


class UserAlreadyVerifiedError(JARSException):
    """Raised when user is already verified"""
    def __init__(self):
        super().__init__("User is already verified", "USER_ALREADY_VERIFIED")


class InvalidVerificationTokenError(JARSException):
    """Raised when email verification token is invalid"""
    def __init__(self, detail: str = "Invalid or expired email verification token"):
        super().__init__(detail, "INVALID_VERIFICATION_TOKEN")


class ExpiredVerificationTokenError(JARSException):
    """Raised when email verification token has expired"""
    def __init__(self, detail: str = "Email verification token has expired"):
        super().__init__(detail, "VERIFICATION_TOKEN_EXPIRED")


class VerificationError(JARSException):
    """Raised when user verification fails"""
    def __init__(self, reason: str = ""):
        detail = f"Failed to verify user: {reason}" if reason else "Failed to verify user"
        super().__init__(detail, "VERIFICATION_FAILED")

class KYCRequiredError(PermissionDeniedError):
    """Raised when KYC verification is required"""
    def __init__(self, detail: str = "KYC verification is required to perform this action"):
        super().__init__(detail)


class KYCPendingError(PermissionDeniedError):
    """Raised when KYC verification is still pending"""
    def __init__(self, detail: str = "KYC verification is still pending"):
        super().__init__(detail)


class KYCRejectedError(JARSException):
    """Raised when KYC verification was rejected"""
    def __init__(self, reason: str = ""):
        detail = f"KYC verification rejected: {reason}" if reason else "KYC verification was rejected"
        super().__init__(detail, "KYC_REJECTED")


class KYCSubmissionError(JARSException):
    """Raised when KYC submission fails"""
    def __init__(self, reason: str = ""):
        detail = f"KYC submission failed: {reason}" if reason else "KYC submission failed"
        super().__init__(detail, "KYC_SUBMISSION_FAILED")

class APIKeyInvalidError(AuthenticationError):
    """Raised when API key is invalid"""
    def __init__(self):
        super().__init__("Invalid API key provided")


class APIKeyRevokedError(AuthenticationError):
    """Raised when API key has been revoked"""
    def __init__(self):
        super().__init__("API key has been revoked")


class APIKeyExpiredError(AuthenticationError):
    """Raised when API key has expired"""
    def __init__(self):
        super().__init__("API key has expired")


class APIKeyCreationError(JARSException):
    """Raised when API key creation fails"""
    def __init__(self, reason: str = ""):
        detail = f"API key creation failed: {reason}" if reason else "API key creation failed"
        super().__init__(detail, "API_KEY_CREATION_FAILED")

class APIKeyNotFoundError(ResourceNotFoundError):
    """Raised when API key is not found"""
    def __init__(self, detail: str = "API key not found"):
        super().__init__(detail)

class TraderProfileCreationError(JARSException):
    """Raised when trader profile creation fails"""
    def __init__(self, reason: str = ""):
        detail = f"Trader profile creation failed: {reason}" if reason else "Trader profile creation failed"
        super().__init__(detail, "TRADER_PROFILE_CREATION_FAILED")

class TraderProfileNotFoundError(ResourceNotFoundError):
    """Raised when trader profile is not found"""
    def __init__(self, detail: str = "Trader profile not found"):
        super().__init__(detail)

class TraderProfileError(JARSException):
    """Raised for general trader profile errors"""
    def __init__(self, detail: str = "Trader profile error"):
        super().__init__(detail, "TRADER_PROFILE_ERROR")

class KYCError(JARSException):
    """Raised for general KYC errors"""
    def __init__(self, detail: str = "KYC error"):
        super().__init__(detail, "KYC_ERROR")

class KYCNotFoundError(ResourceNotFoundError):
    """Raised when KYC record is not found"""
    def __init__(self, detail: str = "KYC record not found"):
        super().__init__(detail)

class APIKeyNotFoundError(ResourceNotFoundError):
    """Raised when API key is not found"""
    def __init__(self, detail: str = "API key not found"):
        super().__init__(detail)

class TraderProfileNotFoundError(ResourceNotFoundError):
    """Raised when trader profile is not found"""
    def __init__(self):
        super().__init__("Trader profile")


class TraderProfileCreationError(JARSException):
    """Raised when trader profile creation fails"""
    def __init__(self, reason: str = ""):
        detail = f"Trader profile creation failed: {reason}" if reason else "Trader profile creation failed"
        super().__init__(detail, "TRADER_PROFILE_CREATION_FAILED")


class TraderNotActiveError(JARSException):
    """Raised when trader is not active for copy trading"""
    def __init__(self, detail: str = "Trader is not active for copy trading"):
        super().__init__(detail, "TRADER_NOT_ACTIVE")

class SubscriptionNotFoundError(ResourceNotFoundError):
    """Raised when subscription is not found"""
    def __init__(self, detail: str = "Subscription not found"):
        super().__init__(detail)


class InsufficientCapitalError(JARSException):
    """Raised when user doesn't have enough capital to follow a trader (Whale validator)"""
    def __init__(self, detail: str = "Insufficient capital to follow this trader"):
        super().__init__(detail, "INSUFFICIENT_CAPITAL")


class SubscriptionCreationError(JARSException):
    """Raised when subscription creation fails"""
    def __init__(self, reason: str = ""):
        detail = f"Subscription creation failed: {reason}" if reason else "Subscription creation failed"
        super().__init__(detail, "SUBSCRIPTION_CREATION_FAILED")


class SubscriptionAlreadyExistsError(JARSException):
    """Raised when subscription already exists"""
    def __init__(self, detail: str = "You are already subscribed to this trader"):
        super().__init__(detail, "SUBSCRIPTION_ALREADY_EXISTS")


class SubscriptionNotActiveError(JARSException):
    """Raised when subscription is not active"""
    def __init__(self, detail: str = "Subscription is not active"):
        super().__init__(detail, "SUBSCRIPTION_NOT_ACTIVE")


class SubscriptionPausedError(JARSException):
    """Raised when subscription is paused"""
    def __init__(self, detail: str = "Subscription is currently paused"):
        super().__init__(detail, "SUBSCRIPTION_PAUSED")

class UpgradeRequiredError(JARSException):
    """Raised when the current Subscription tier doesn't cover that intended action"""
    def __init__(self, detail: str = "Upgrade required"):
        super().__init__(detail, "UPGRADE_REQUIRED")


class SelfSubscriptionError(JARSException):
    """Raised when user tries to subscribe to themselves"""
    def __init__(self):
        super().__init__("Cannot subscribe to your own trading profile", "SELF_SUBSCRIPTION_NOT_ALLOWED")

class SignalNotFoundError(ResourceNotFoundError):
    """Raised when signal is not found"""
    def __init__(self):
        super().__init__("Signal")


class SignalCreationError(JARSException):
    """Raised when signal creation fails"""
    def __init__(self, reason: str = ""):
        detail = f"Signal creation failed: {reason}" if reason else "Signal creation failed"
        super().__init__(detail, "SIGNAL_CREATION_FAILED")


class SignalExpiredError(JARSException):
    """Raised when signal has expired"""
    def __init__(self, detail: str = "Signal has expired"):
        super().__init__(detail, "SIGNAL_EXPIRED")


class InvalidSignalError(JARSException):
    """Raised when signal is invalid"""
    def __init__(self, detail: str = "Invalid signal"):
        super().__init__(detail, "INVALID_SIGNAL")


class TradeNotFoundError(ResourceNotFoundError):
    """Raised when trade is not found"""
    def __init__(self):
        super().__init__("Trade")


class TradeCreationError(JARSException):
    """Raised when trade creation fails"""
    def __init__(self, reason: str = ""):
        detail = f"Trade creation failed: {reason}" if reason else "Trade creation failed"
        super().__init__(detail, "TRADE_CREATION_FAILED")


class TradeExecutionError(JARSException):
    """Raised when trade execution fails"""
    def __init__(self, reason: str = ""):
        detail = f"Trade execution failed: {reason}" if reason else "Trade execution failed"
        super().__init__(detail, "TRADE_EXECUTION_FAILED")


class InvalidTradeAmountError(InvalidRequestError):
    """Raised when trade amount is invalid"""
    def __init__(self, detail: str = "Trade amount must be a positive value"):
        super().__init__(detail)


class InsufficientAllocationError(JARSException):
    """Raised when allocation is insufficient for trade"""
    def __init__(self, detail: str = "Insufficient allocation for this trade"):
        super().__init__(detail, "INSUFFICIENT_ALLOCATION")


class DuplicateTradeError(JARSException):
    """Raised when a duplicate trade is detected"""
    def __init__(self, detail: str = "A trade with this idempotency key already exists"):
        super().__init__(detail, "DUPLICATE_TRADE")


class TradeCopyError(JARSException):
    """Raised when copying a trade fails"""
    def __init__(self, reason: str = ""):
        detail = f"Failed to copy trade: {reason}" if reason else "Failed to copy trade"
        super().__init__(detail, "TRADE_COPY_FAILED")


class LedgerError(JARSException):
    """Base error for ledger operations"""
    def __init__(self, detail: str = "Ledger operation failed"):
        super().__init__(detail, "LEDGER_ERROR")


class InsufficientBalanceError(JARSException):
    """Raised when balance is insufficient"""
    def __init__(self, detail: str = "Insufficient balance for this operation"):
        super().__init__(detail, "INSUFFICIENT_BALANCE")


class DepositError(JARSException):
    """Raised when deposit fails"""
    def __init__(self, reason: str = ""):
        detail = f"Deposit failed: {reason}" if reason else "Deposit failed"
        super().__init__(detail, "DEPOSIT_FAILED")


class WithdrawalError(JARSException):
    """Raised when withdrawal fails"""
    def __init__(self, reason: str = ""):
        detail = f"Withdrawal failed: {reason}" if reason else "Withdrawal failed"
        super().__init__(detail, "WITHDRAWAL_FAILED")

class ExchangeRateError(JARSException):
    """Raised when exchange rate retrieval fails"""
    def __init__(self, reason: str = ""):
        detail = f"Exchange rate retrieval failed: {reason}" if reason else "Exchange rate retrieval failed"
        super().__init__(detail, "EXCHANGE_RATE_ERROR")

class InvalidAmountError(InvalidRequestError):
    """Raised when amount is invalid"""
    def __init__(self, detail: str = "Amount must be a positive value"):
        super().__init__(detail)


class TransactionNotFoundError(ResourceNotFoundError):
    """Raised when transaction is not found"""
    def __init__(self, detail: str = "Transaction not found"):
        super().__init__(detail)


class DuplicateTransactionError(JARSException):
    """Raised when a duplicate transaction is detected"""
    def __init__(self, detail: str = "Transaction already exists"):
        super().__init__(detail, "DUPLICATE_TRANSACTION")


class InvalidTransactionStateError(JARSException):
    """Raised when transaction is in invalid state"""
    def __init__(self, detail: str = "Transaction is in invalid state"):
        super().__init__(detail, "INVALID_TRANSACTION_STATE")


class AccountNotFoundError(ResourceNotFoundError):
    """Raised when account is not found"""
    def __init__(self, detail: str = "Account not found"):
        super().__init__(detail)


class SystemAccountNotFoundError(ResourceNotFoundError):
    """Raised when system account is not found (should be created via seed script)"""
    def __init__(self, detail: str = "System account not found"):
        super().__init__(detail)


class InsufficientFundsError(JARSException):
    """Raised when funds are insufficient"""
    def __init__(self, detail: str = "Insufficient funds"):
        super().__init__(detail, "INSUFFICIENT_FUNDS")


class PaystackWebhookError(JARSException):
    """Raised when Paystack webhook processing fails"""
    def __init__(self, detail: str = "Paystack webhook error"):
        super().__init__(detail, "PAYSTACK_WEBHOOK_ERROR")


class InvalidWebhookSignatureError(AuthenticationError):
    """Raised when webhook signature is invalid"""
    def __init__(self):
        super().__init__("Invalid webhook signature")


class FeeCalculationError(JARSException):
    """Raised when fee calculation fails"""
    def __init__(self, reason: str = ""):
        detail = f"Fee calculation failed: {reason}" if reason else "Fee calculation failed"
        super().__init__(detail, "FEE_CALCULATION_FAILED")


def exception_to_http_response(exc: JARSException, status_code: int = status.HTTP_400_BAD_REQUEST):
    """Converts a custom exception into a standardized HTTPException."""
    return HTTPException(
        status_code=status_code,
        detail={"error": exc.code, "message": exc.detail}
    )


EXCEPTION_STATUS_MAP = {
    InvalidRequestError: status.HTTP_400_BAD_REQUEST,
    InvalidTradeAmountError: status.HTTP_400_BAD_REQUEST,
    InvalidAmountError: status.HTTP_400_BAD_REQUEST,
    InvalidSignalError: status.HTTP_400_BAD_REQUEST,
    PasswordMismatchError: status.HTTP_400_BAD_REQUEST,
    SelfSubscriptionError: status.HTTP_400_BAD_REQUEST,

    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    InvalidCredentialsError: status.HTTP_401_UNAUTHORIZED,
    TokenExpiredError: status.HTTP_401_UNAUTHORIZED,
    InvalidTokenError: status.HTTP_401_UNAUTHORIZED,
    RefreshTokenExpiredError: status.HTTP_401_UNAUTHORIZED,
    APIKeyInvalidError: status.HTTP_401_UNAUTHORIZED,
    APIKeyRevokedError: status.HTTP_401_UNAUTHORIZED,
    APIKeyExpiredError: status.HTTP_401_UNAUTHORIZED,

    PermissionDeniedError: status.HTTP_403_FORBIDDEN,
    KYCRequiredError: status.HTTP_403_FORBIDDEN,
    KYCPendingError: status.HTTP_403_FORBIDDEN,

    ResourceNotFoundError: status.HTTP_404_NOT_FOUND,
    UserNotFoundError: status.HTTP_404_NOT_FOUND,
    TraderProfileNotFoundError: status.HTTP_404_NOT_FOUND,
    SubscriptionNotFoundError: status.HTTP_404_NOT_FOUND,
    SignalNotFoundError: status.HTTP_404_NOT_FOUND,
    TradeNotFoundError: status.HTTP_404_NOT_FOUND,
    TransactionNotFoundError: status.HTTP_404_NOT_FOUND,

    DuplicateEmailError: status.HTTP_409_CONFLICT,
    SubscriptionAlreadyExistsError: status.HTTP_409_CONFLICT,
    DuplicateTradeError: status.HTTP_409_CONFLICT,
    UserAlreadyVerifiedError: status.HTTP_409_CONFLICT,

    InsufficientBalanceError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    InsufficientAllocationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    TradeExecutionError: status.HTTP_422_UNPROCESSABLE_ENTITY,

    RateLimitExceededError: status.HTTP_429_TOO_MANY_REQUESTS,

    DatabaseError: status.HTTP_500_INTERNAL_SERVER_ERROR,

    ServiceUnavailableError: status.HTTP_503_SERVICE_UNAVAILABLE,
}


def get_http_status_for_exception(exc: JARSException) -> int:
    for exc_type, status_code in EXCEPTION_STATUS_MAP.items():
        if isinstance(exc, exc_type):
            return status_code
    return status.HTTP_400_BAD_REQUEST


def raise_http_exception(exc: JARSException):
    raise exception_to_http_response(exc, get_http_status_for_exception(exc))
