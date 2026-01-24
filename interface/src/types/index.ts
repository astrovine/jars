
export interface User {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  status: "PENDING" | "VERIFIED" | "SUSPENDED";
  country: string | null;
  is_active: boolean;
  is_2fa_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserFull extends User {
  kyc: KYCSummary | null;
  trader_profile: TraderProfileSummary | null;
}

export interface KYCSummary {
  status: string;
  first_name: string;
  last_name: string;
  country: string;
}

export interface TraderProfileSummary {
  id: string;
  alias: string;
  is_active: boolean;
  performance_fee_percentage: number;
}

export interface UserCreate {
  first_name: string;
  last_name: string;
  email: string;
  country: string;
  phone_number?: string;
  password: string;
}

export interface LoginResponse {
  require_2fa: boolean;
  access_token?: string;
  refresh_token?: string;
  pre_auth_token?: string;
  token_type?: string;
  message?: string;
}

export interface TwoFactorSetupResponse {
  secret: string;
  qr_code_uri: string;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// ============================================================================
// Trader Profile Types
// ============================================================================

export type TraderStatus = "DRAFT" | "PENDING" | "INCUBATION" | "ACTIVE" | "SUSPENDED";

export interface TraderProfile {
  id: string;
  user_id: string;
  alias: string;
  bio: string | null;
  status: TraderStatus;
  is_active: boolean;
  performance_fee_percentage: number;
  min_allocation_amount: number;
  max_allocation_amount: number | null;
  max_subscribers: number | null;
  current_subscribers: number;
  total_pnl: number;
  win_rate: number;
  total_trades: number;
  created_at: string;
  updated_at: string;
}

export interface TraderProfileCreate {
  alias: string;
  bio?: string;
  performance_fee_percentage?: number;
  min_allocation_amount?: number;
  max_allocation_amount?: number;
  max_subscribers?: number;
}

// ============================================================================
// KYC Types
// ============================================================================

export type KYCStatus = "PENDING" | "APPROVED" | "REJECTED";

export interface KYC {
  id: string;
  user_id: string;
  first_name: string;
  last_name: string;
  country: string;
  date_of_birth: string | null;
  past_trades: string | null;
  id_document_url: string | null;
  status: KYCStatus;
  rejection_reason: string | null;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// Exchange Keys Types
// ============================================================================

export type ExchangeName = "binance" | "bybit" | "okx";

export interface ExchangeKey {
  id: string;
  user_id: string;
  exchange_name: ExchangeName;
  label: string;
  api_key_masked: string;
  is_active: boolean;
  is_valid: boolean;
  permissions: string[];
  last_used_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExchangeKeyCreate {
  exchange_name: ExchangeName;
  label: string;
  api_key: string;
  api_secret: string;
  passphrase?: string;
}

// ============================================================================
// Subscription Types
// ============================================================================

export type SubscriptionStatus = "ACTIVE" | "PAUSED" | "STOPPED";
export type CopyMode = "PROPORTIONAL" | "FIXED";

export interface Subscription {
  id: string;
  follower_id: string;
  leader_profile_id: string;
  allocation_amount: number;
  copy_mode: CopyMode;
  status: SubscriptionStatus;
  total_copied_trades: number;
  total_pnl: number;
  created_at: string;
  updated_at: string;
  paused_at: string | null;
  stopped_at: string | null;
  leader_profile?: TraderProfile;
}

export interface SubscriptionCreate {
  leader_profile_id: string;
  allocation_amount: number;
  copy_mode?: CopyMode;
}

export interface SubscriptionUpdate {
  allocation_amount?: number;
  copy_mode?: CopyMode;
  status?: "ACTIVE" | "PAUSED";
}

// ============================================================================
// Trade Types
// ============================================================================

export type OrderSide = "BUY" | "SELL";
export type OrderType = "MARKET" | "LIMIT";
export type TradeStatus = "PENDING" | "EXECUTED" | "FAILED" | "CANCELLED";

export interface Trade {
  id: string;
  subscription_id: string;
  symbol: string;
  side: OrderSide;
  order_type: OrderType;
  quantity: number;
  price: number;
  executed_quantity: number | null;
  executed_price: number | null;
  fee: number;
  fee_asset: string;
  status: TradeStatus;
  pnl: number | null;
  latency_ms: number;
  exchange_order_id: string | null;
  created_at: string;
  executed_at: string | null;
}

// ============================================================================
// Ledger Types
// ============================================================================

export type TransactionType =
  | "DEPOSIT"
  | "WITHDRAWAL"
  | "TRADE_PNL"
  | "FEE"
  | "PROFIT_SHARE"
  | "REFERRAL"
  | "ADJUSTMENT";

export interface LedgerEntry {
  id: string;
  account_id: string;
  transaction_type: TransactionType;
  amount: number;
  currency: string;
  balance_before: number;
  balance_after: number;
  description: string;
  reference: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface LedgerAccount {
  id: string;
  user_id: string;
  currency: string;
  type: string;
  balance: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// Wallet Types
// ============================================================================

export interface WalletBalance {
  total: number;
  available: number;
  locked: number;
  currency: string;
}

// ============================================================================
// Audit Log Types
// ============================================================================

export interface AuditLog {
  id: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  ip_address: string | null;
  user_agent: string | null;
  changes: Record<string, unknown> | null;
  extra_data: Record<string, unknown> | null;
  created_at: string;
}

// ============================================================================
// API Response Types
// ============================================================================

export interface APIError {
  error: string;
  message: string;
  details?: Record<string, string[]>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ============================================================================
// WebSocket Message Types
// ============================================================================

export interface WSMessage {
  type: string;
  payload?: unknown;
  timestamp?: string;
}

export interface WSSystemStatus extends WSMessage {
  type: "system_status";
  payload: {
    sentinel: "connected" | "disconnected";
    exchange: "connected" | "disconnected";
    executionLatency: number;
  };
}

export interface WSTradeSignal extends WSMessage {
  type: "trade_signal";
  payload: {
    traderId: string;
    symbol: string;
    side: OrderSide;
    price: number;
    quantity: number;
    timestamp: string;
  };
}

export interface WSTradeExecuted extends WSMessage {
  type: "trade_executed";
  payload: {
    tradeId: string;
    subscriptionId: string;
    symbol: string;
    side: OrderSide;
    executedQuantity: number;
    executedPrice: number;
    latency: number;
    status: "executed" | "failed";
    error?: string;
  };
}

export interface WSBalanceUpdate extends WSMessage {
  type: "balance_update";
  payload: {
    accountId: string;
    balance: number;
    available: number;
    locked: number;
  };
}

