import enum


class CopyMode(str, enum.Enum):
    PROPORTIONAL = "proportional"
    FIXED_AMOUNT = "fixed_amount"


class OrderSide(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, enum.Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class TradeStatus(str, enum.Enum):
    PENDING = "pending"
    FILLED = "filled"
    FAILED = "failed"
    PARTIALLY_FILLED = "partially_filled"


class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRADE_PROFIT = "trade_profit"
    PERFORMANCE_FEE = "performance_fee"
    SUBSCRIPTION_FEE = "subscription_fee"
    VIRTUAL_ISSUANCE = "virtual_issuance"
    VIRTUAL_RESET = "virtual_reset"
    VIRTUAL_RESET_FREE = "virtual_reset_free"


class TraderProfileStatus(str, enum.Enum):
    DRAFT = 'draft'
    PENDING_KYC = 'pending'
    INCUBATION = 'incubation'
    PROBATION = 'probation'
    ACTIVE = 'active'
    SUSPENDED = 'suspended'

class VerificationStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class AccountType(enum.Enum):
    SYSTEM_FEE_WALLET = "system_fee_wallet"
    SYSTEM_BANK_SETTLEMENT = "system_bank_settlement" #paystack
    SYSTEM_BANK_BALANCE = "system_bank_balance" #I want to keep track of the system balance for demo funding
    USER_LIVE_WALLET = "user_live_wallet"
    USER_DEMO_WALLET = "user_demo_wallet"


class EntryDirection(enum.Enum):
    DEBIT = "debit"
    CREDIT = "credit"

class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REVERSED = "reversed"

class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    PLUS = "plus"
    BUSINESS = "business"

class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    LIQUIDATED = "liquidated"
    INACTIVE = 'inactive'

class SubscriptionTierStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    RENEWED = "renewed"


class UserTier(str, enum.Enum):
    FREE = "free"
    PLUS = "plus"
    BUSINESS = "business"
