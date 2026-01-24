/**
 * JARS API Client
 * Proper integration with FastAPI backend
 */

import type {
  User,
  UserFull,
  UserCreate,
  LoginResponse,
  Token,
  TwoFactorSetupResponse,
  TraderProfile,
  TraderProfileCreate,
  ExchangeKey,
  ExchangeKeyCreate,
  Subscription,
  SubscriptionCreate,
  SubscriptionUpdate,
  Trade,
  LedgerEntry,
  LedgerAccount,
  AuditLog,
  PaginatedResponse,
  APIError,
} from "@/types";

// API Base URL - connects to your Docker backend
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

/**
 * Custom API Error
 */
export class APIClientError extends Error {
  code: string;
  status: number;

  constructor(message: string, code: string, status: number) {
    super(message);
    this.name = "APIClientError";
    this.code = code;
    this.status = status;
  }
}

/**
 * Token Storage
 */
class TokenManager {
  private static ACCESS_TOKEN_KEY = "jars_access_token";
  private static REFRESH_TOKEN_KEY = "jars_refresh_token";

  static getAccessToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(this.ACCESS_TOKEN_KEY);
  }

  static setAccessToken(token: string): void {
    if (typeof window === "undefined") return;
    localStorage.setItem(this.ACCESS_TOKEN_KEY, token);
  }

  static getRefreshToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  static setRefreshToken(token: string): void {
    if (typeof window === "undefined") return;
    localStorage.setItem(this.REFRESH_TOKEN_KEY, token);
  }

  static setTokens(accessToken: string, refreshToken: string): void {
    this.setAccessToken(accessToken);
    this.setRefreshToken(refreshToken);
  }

  static clearTokens(): void {
    if (typeof window === "undefined") return;
    localStorage.removeItem(this.ACCESS_TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
  }

  static hasTokens(): boolean {
    return !!this.getAccessToken();
  }
}

export { TokenManager };

/**
 * Base fetch wrapper with auth and error handling
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  requireAuth: boolean = true
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  // Add auth header if we have a token
  if (requireAuth) {
    const token = TokenManager.getAccessToken();
    if (token) {
      (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
    }
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      credentials: "include", // Include cookies for httpOnly tokens
    });

    // Handle 401 - attempt token refresh
    if (response.status === 401 && requireAuth) {
      const refreshed = await attemptTokenRefresh();
      if (refreshed) {
        // Retry with new token
        const newToken = TokenManager.getAccessToken();
        if (newToken) {
          (headers as Record<string, string>)["Authorization"] = `Bearer ${newToken}`;
        }
        const retryResponse = await fetch(url, { ...options, headers, credentials: "include" });
        return handleResponse<T>(retryResponse);
      } else {
        TokenManager.clearTokens();
        if (typeof window !== "undefined") {
          window.location.href = "/login?session_expired=true";
        }
        throw new APIClientError("Session expired", "SESSION_EXPIRED", 401);
      }
    }

    return handleResponse<T>(response);
  } catch (error) {
    if (error instanceof APIClientError) {
      throw error;
    }
    // Network error
    console.error("[API] Network error:", error);
    throw new APIClientError("Network error. Please check your connection.", "NETWORK_ERROR", 0);
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorData: APIError;
    try {
      errorData = await response.json();
    } catch {
      errorData = { error: "UNKNOWN_ERROR", message: response.statusText };
    }
    throw new APIClientError(
      errorData.message || "An error occurred",
      errorData.error || "UNKNOWN_ERROR",
      response.status
    );
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

async function attemptTokenRefresh(): Promise<boolean> {
  const refreshToken = TokenManager.getRefreshToken();
  if (!refreshToken) return false;

  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
      credentials: "include",
    });

    if (!response.ok) return false;

    const data: Token = await response.json();
    TokenManager.setTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

// ============================================================================
// Authentication API
// ============================================================================

export const authAPI = {
  /**
   * Register a new user
   * POST /auth/register
   */
  register: async (data: UserCreate): Promise<User> => {
    return apiRequest<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }, false);
  },

  /**
   * Login with email and password
   * POST /auth/login (OAuth2 form data)
   */
  login: async (email: string, password: string): Promise<LoginResponse> => {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData,
      credentials: "include",
    });

    const data = await handleResponse<LoginResponse>(response);

    // Store tokens if login successful (no 2FA required)
    if (!data.require_2fa && data.access_token && data.refresh_token) {
      TokenManager.setTokens(data.access_token, data.refresh_token);
    }

    return data;
  },

  /**
   * Verify 2FA code during login
   * POST /auth/2fa/verify
   */
  verify2FA: async (preAuthToken: string, code: string): Promise<Token> => {
    const data = await apiRequest<Token>("/auth/2fa/verify", {
      method: "POST",
      body: JSON.stringify({ pre_auth_token: preAuthToken, code }),
    }, false);

    TokenManager.setTokens(data.access_token, data.refresh_token);
    return data;
  },

  /**
   * Setup 2FA - get secret and QR code
   * POST /auth/2fa/setup
   */
  setup2FA: async (): Promise<TwoFactorSetupResponse> => {
    return apiRequest<TwoFactorSetupResponse>("/auth/2fa/setup", {
      method: "POST",
    });
  },

  /**
   * Confirm 2FA setup with verification code
   * POST /auth/2fa/confirm
   */
  confirm2FA: async (secret: string, code: string): Promise<{ message: string }> => {
    return apiRequest<{ message: string }>("/auth/2fa/confirm", {
      method: "POST",
      body: JSON.stringify({ secret, code }),
    });
  },

  /**
   * Disable 2FA
   * POST /auth/2fa/disable
   */
  disable2FA: async (code: string): Promise<{ message: string }> => {
    return apiRequest<{ message: string }>("/auth/2fa/disable", {
      method: "POST",
      body: JSON.stringify({ code }),
    });
  },

  /**
   * Refresh access token
   * POST /auth/refresh
   */
  refreshToken: async (): Promise<Token> => {
    const refreshToken = TokenManager.getRefreshToken();
    if (!refreshToken) {
      throw new APIClientError("No refresh token", "NO_REFRESH_TOKEN", 401);
    }

    const data = await apiRequest<Token>("/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    }, false);

    TokenManager.setTokens(data.access_token, data.refresh_token);
    return data;
  },

  /**
   * Logout - clear tokens
   * POST /auth/logout
   */
  logout: async (): Promise<void> => {
    try {
      await apiRequest<void>("/auth/logout", { method: "POST" });
    } finally {
      TokenManager.clearTokens();
    }
  },

  /**
   * Request email verification resend
   * POST /auth/resend-verification
   */
  resendVerification: async (email: string): Promise<{ message: string }> => {
    return apiRequest<{ message: string }>(`/auth/resend-verification?email=${encodeURIComponent(email)}`, {
      method: "POST",
    }, false);
  },

  /**
   * Verify email with token
   * POST /auth/verify-email
   */
  verifyEmail: async (token: string): Promise<{ message: string }> => {
    return apiRequest<{ message: string }>(`/auth/verify-email?token=${token}`, {
      method: "POST",
    }, false);
  },

  /**
   * Request password reset
   * POST /auth/forgot-password
   */
  forgotPassword: async (email: string): Promise<{ message: string }> => {
    return apiRequest<{ message: string }>("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    }, false);
  },

  /**
   * Reset password with token
   * POST /auth/reset-password
   */
  resetPassword: async (token: string, newPassword: string): Promise<{ message: string }> => {
    return apiRequest<{ message: string }>("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ token, new_password: newPassword }),
    }, false);
  },

  /**
   * Change password (authenticated)
   * POST /auth/change-password
   */
  changePassword: async (oldPassword: string, newPassword: string, confirmPassword: string): Promise<{ message: string }> => {
    return apiRequest<{ message: string }>("/auth/change-password", {
      method: "POST",
      body: JSON.stringify({
        old_password: oldPassword,
        new_password: newPassword,
        confirm_password: confirmPassword,
      }),
    });
  },
};

// ============================================================================
// Users API
// ============================================================================

export const usersAPI = {
  /**
   * Get current user basic info
   * GET /users/me
   */
  getCurrentUser: async (): Promise<User> => {
    return apiRequest<User>("/users/me");
  },

  /**
   * Get current user with KYC and trader profile
   * GET /users/me/full
   */
  getCurrentUserFull: async (): Promise<UserFull> => {
    return apiRequest<UserFull>("/users/me/full");
  },

  /**
   * Refresh user data
   * GET /users/me/refresh
   */
  refreshUserData: async (): Promise<UserFull> => {
    return apiRequest<UserFull>("/users/me/refresh");
  },

  /**
   * Update user profile
   * PATCH /users/me
   */
  updateProfile: async (data: { first_name?: string; last_name?: string; country?: string }): Promise<User> => {
    return apiRequest<User>("/users/me", {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  /**
   * Get user audit logs
   * GET /users/me/audit-logs
   */
  getAuditLogs: async (page: number = 1, pageSize: number = 20): Promise<PaginatedResponse<AuditLog>> => {
    return apiRequest<PaginatedResponse<AuditLog>>(`/users/me/audit-logs?page=${page}&page_size=${pageSize}`);
  },
};

// ============================================================================
// Traders API
// ============================================================================

export const tradersAPI = {
  /**
   * Apply to become a trader
   * POST /traders/apply
   */
  apply: async (data: TraderProfileCreate): Promise<TraderProfile> => {
    return apiRequest<TraderProfile>("/traders/apply", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /**
   * Get all active traders (for copy trading)
   * GET /traders
   */
  getAll: async (params?: {
    page?: number;
    page_size?: number;
    sort_by?: string;
    min_roi?: number;
  }): Promise<PaginatedResponse<TraderProfile>> => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set("page", params.page.toString());
    if (params?.page_size) searchParams.set("page_size", params.page_size.toString());
    if (params?.sort_by) searchParams.set("sort_by", params.sort_by);
    if (params?.min_roi) searchParams.set("min_roi", params.min_roi.toString());

    return apiRequest<PaginatedResponse<TraderProfile>>(`/traders?${searchParams.toString()}`);
  },

  /**
   * Get trader by ID
   * GET /traders/:id
   */
  getById: async (id: string): Promise<TraderProfile> => {
    return apiRequest<TraderProfile>(`/traders/${id}`);
  },

  /**
   * Get trader's trade history
   * GET /traders/:id/trades
   */
  getTrades: async (id: string, page: number = 1, pageSize: number = 20): Promise<PaginatedResponse<Trade>> => {
    return apiRequest<PaginatedResponse<Trade>>(`/traders/${id}/trades?page=${page}&page_size=${pageSize}`);
  },

  /**
   * Submit KYC documents
   * POST /traders/kyc/submit (multipart form data)
   */
  submitKYC: async (data: {
    first_name: string;
    last_name: string;
    country: string;
    date_of_birth?: string;
    past_trades?: string;
    id_document: File;
  }): Promise<{ message: string }> => {
    const formData = new FormData();
    formData.append("first_name", data.first_name);
    formData.append("last_name", data.last_name);
    formData.append("country", data.country);
    if (data.date_of_birth) formData.append("date_of_birth", data.date_of_birth);
    if (data.past_trades) formData.append("past_trades", data.past_trades);
    formData.append("id_document", data.id_document);

    const token = TokenManager.getAccessToken();
    const response = await fetch(`${API_BASE_URL}/traders/kyc/submit`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
      credentials: "include",
    });

    return handleResponse<{ message: string }>(response);
  },

  /**
   * Get my trader profile
   * GET /traders/me
   */
  getMyProfile: async (): Promise<TraderProfile> => {
    return apiRequest<TraderProfile>("/traders/me");
  },

  /**
   * Update my trader profile
   * PATCH /traders/me
   */
  updateMyProfile: async (data: Partial<TraderProfileCreate>): Promise<TraderProfile> => {
    return apiRequest<TraderProfile>("/traders/me", {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },
};

// ============================================================================
// Exchange Keys API
// ============================================================================

export const keysAPI = {
  /**
   * Create new exchange key
   * POST /keys
   */
  create: async (data: ExchangeKeyCreate): Promise<ExchangeKey> => {
    return apiRequest<ExchangeKey>("/keys", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /**
   * Get all exchange keys
   * GET /keys
   */
  getAll: async (exchange?: string): Promise<ExchangeKey[]> => {
    const params = exchange ? `?exchange=${exchange}` : "";
    return apiRequest<ExchangeKey[]>(`/keys${params}`);
  },

  /**
   * Get exchange key by ID
   * GET /keys/:id
   */
  getById: async (id: string): Promise<ExchangeKey> => {
    return apiRequest<ExchangeKey>(`/keys/${id}`);
  },

  /**
   * Update exchange key
   * PATCH /keys/:id
   */
  update: async (id: string, data: { label?: string; is_active?: boolean }): Promise<ExchangeKey> => {
    return apiRequest<ExchangeKey>(`/keys/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete (revoke) exchange key
   * DELETE /keys/:id
   */
  revoke: async (id: string): Promise<void> => {
    return apiRequest<void>(`/keys/${id}`, { method: "DELETE" });
  },

  /**
   * Validate exchange key
   * POST /keys/:id/validate
   */
  validate: async (id: string): Promise<{ valid: boolean; permissions: string[] }> => {
    return apiRequest<{ valid: boolean; permissions: string[] }>(`/keys/${id}/validate`, {
      method: "POST",
    });
  },
};

// ============================================================================
// Subscriptions API
// ============================================================================

export const subscriptionsAPI = {
  /**
   * Create new subscription (start copying a trader)
   * POST /subscriptions
   */
  create: async (data: SubscriptionCreate): Promise<Subscription> => {
    return apiRequest<Subscription>("/subscriptions", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /**
   * Get all my subscriptions
   * GET /subscriptions
   */
  getAll: async (status?: string): Promise<Subscription[]> => {
    const params = status ? `?status=${status}` : "";
    return apiRequest<Subscription[]>(`/subscriptions${params}`);
  },

  /**
   * Get subscription by ID
   * GET /subscriptions/:id
   */
  getById: async (id: string): Promise<Subscription> => {
    return apiRequest<Subscription>(`/subscriptions/${id}`);
  },

  /**
   * Update subscription
   * PATCH /subscriptions/:id
   */
  update: async (id: string, data: SubscriptionUpdate): Promise<Subscription> => {
    return apiRequest<Subscription>(`/subscriptions/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  /**
   * Pause subscription
   * POST /subscriptions/:id/pause
   */
  pause: async (id: string): Promise<Subscription> => {
    return apiRequest<Subscription>(`/subscriptions/${id}/pause`, { method: "POST" });
  },

  /**
   * Resume subscription
   * POST /subscriptions/:id/resume
   */
  resume: async (id: string): Promise<Subscription> => {
    return apiRequest<Subscription>(`/subscriptions/${id}/resume`, { method: "POST" });
  },

  /**
   * Stop subscription (permanent)
   * POST /subscriptions/:id/stop
   */
  stop: async (id: string): Promise<Subscription> => {
    return apiRequest<Subscription>(`/subscriptions/${id}/stop`, { method: "POST" });
  },

  /**
   * Get trades for a subscription
   * GET /subscriptions/:id/trades
   */
  getTrades: async (id: string, page: number = 1, pageSize: number = 20): Promise<PaginatedResponse<Trade>> => {
    return apiRequest<PaginatedResponse<Trade>>(`/subscriptions/${id}/trades?page=${page}&page_size=${pageSize}`);
  },

  /**
   * Pause all subscriptions (emergency)
   * POST /subscriptions/pause-all
   */
  pauseAll: async (): Promise<{ message: string; paused_count: number }> => {
    return apiRequest<{ message: string; paused_count: number }>("/subscriptions/pause-all", { method: "POST" });
  },
};

// ============================================================================
// Wallet API
// ============================================================================

export const walletAPI = {
  /**
   * Get wallet balance
   * GET /wallet/balance
   */
  getBalance: async (): Promise<LedgerAccount[]> => {
    return apiRequest<LedgerAccount[]>("/wallet/balance");
  },

  /**
   * Get ledger entries
   * GET /wallet/ledger
   */
  getLedger: async (params?: {
    page?: number;
    page_size?: number;
    transaction_type?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<PaginatedResponse<LedgerEntry>> => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set("page", params.page.toString());
    if (params?.page_size) searchParams.set("page_size", params.page_size.toString());
    if (params?.transaction_type) searchParams.set("transaction_type", params.transaction_type);
    if (params?.start_date) searchParams.set("start_date", params.start_date);
    if (params?.end_date) searchParams.set("end_date", params.end_date);

    return apiRequest<PaginatedResponse<LedgerEntry>>(`/wallet/ledger?${searchParams.toString()}`);
  },

  /**
   * Initiate deposit
   * POST /wallet/deposit
   */
  initiateDeposit: async (amount: number, currency: string): Promise<{ payment_url: string; reference: string }> => {
    return apiRequest<{ payment_url: string; reference: string }>("/wallet/deposit", {
      method: "POST",
      body: JSON.stringify({ amount, currency }),
    });
  },

  /**
   * Request withdrawal
   * POST /wallet/withdraw
   */
  requestWithdrawal: async (amount: number, currency: string, bank_account_id: string): Promise<{ reference: string; status: string }> => {
    return apiRequest<{ reference: string; status: string }>("/wallet/withdraw", {
      method: "POST",
      body: JSON.stringify({ amount, currency, bank_account_id }),
    });
  },
};

export const waitlistAPI = {
  join: async (email: string): Promise<{ message: string }> => {
    return apiRequest<{ message: string }>("/waitlist", {
      method: "POST",
      body: JSON.stringify({ email }),
    }, false);
  },
};

// ============================================================================
// Health Check
// ============================================================================

export const healthAPI = {
  /**
   * Check API health
   * GET /health
   */
  check: async (): Promise<{ status: string; service: string }> => {
    const response = await fetch(`${API_BASE_URL.replace("/api/v1", "")}/health`);
    return response.json();
  },
};

