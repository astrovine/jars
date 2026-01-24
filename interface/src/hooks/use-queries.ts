/**
 * React Query Hooks for JARS API
 * Properly integrated with backend endpoints
 */

"use client";

import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
  type UseMutationOptions,
} from "@tanstack/react-query";
import {
  authAPI,
  usersAPI,
  tradersAPI,
  keysAPI,
  subscriptionsAPI,
  walletAPI,
  healthAPI,
  waitlistAPI,
  TokenManager,
} from "@/lib/api";
import { useAuthStore } from "@/lib/stores";
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
} from "@/types";

// ============================================================================
// Query Keys
// ============================================================================

export const queryKeys = {
  // Auth & User
  currentUser: ["currentUser"] as const,
  currentUserFull: ["currentUserFull"] as const,
  auditLogs: (page: number) => ["auditLogs", page] as const,

  // Traders
  traders: ["traders"] as const,
  tradersList: (params?: Record<string, unknown>) => ["traders", "list", params] as const,
  trader: (id: string) => ["traders", id] as const,
  traderTrades: (id: string, page: number) => ["traders", id, "trades", page] as const,
  myTraderProfile: ["myTraderProfile"] as const,

  // Exchange Keys
  exchangeKeys: ["exchangeKeys"] as const,
  exchangeKey: (id: string) => ["exchangeKeys", id] as const,

  // Subscriptions
  subscriptions: ["subscriptions"] as const,
  subscription: (id: string) => ["subscriptions", id] as const,
  subscriptionTrades: (id: string, page: number) => ["subscriptions", id, "trades", page] as const,

  // Wallet
  walletBalance: ["walletBalance"] as const,
  ledger: (params?: Record<string, unknown>) => ["ledger", params] as const,

  // Health
  health: ["health"] as const,
};

// ============================================================================
// Health Check Hook
// ============================================================================

export function useHealthCheck() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: healthAPI.check,
    staleTime: 30 * 1000,
    refetchInterval: 60 * 1000,
    retry: 3,
  });
}

// ============================================================================
// Auth Hooks
// ============================================================================

export function useRegister(
  options?: UseMutationOptions<User, Error, UserCreate>
) {
  return useMutation({
    mutationFn: authAPI.register,
    ...options,
  });
}

export function useLogin(
  options?: UseMutationOptions<LoginResponse, Error, { email: string; password: string }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ email, password }) => authAPI.login(email, password),
    onSuccess: (data) => {
      if (!data.require_2fa) {
        // Tokens are stored in authAPI.login
        queryClient.invalidateQueries({ queryKey: queryKeys.currentUser });
      }
    },
    ...options,
  });
}

export function useVerify2FA(
  options?: UseMutationOptions<Token, Error, { preAuthToken: string; code: string }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ preAuthToken, code }) => authAPI.verify2FA(preAuthToken, code),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.currentUser });
    },
    ...options,
  });
}

export function useSetup2FA(
  options?: UseMutationOptions<TwoFactorSetupResponse, Error, void>
) {
  return useMutation({
    mutationFn: authAPI.setup2FA,
    ...options,
  });
}

export function useConfirm2FA(
  options?: UseMutationOptions<{ message: string }, Error, { secret: string; code: string }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ secret, code }) => authAPI.confirm2FA(secret, code),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.currentUser });
      queryClient.invalidateQueries({ queryKey: queryKeys.currentUserFull });
    },
    ...options,
  });
}

export function useDisable2FA(
  options?: UseMutationOptions<{ message: string }, Error, string>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authAPI.disable2FA,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.currentUser });
    },
    ...options,
  });
}

export function useLogout(options?: UseMutationOptions<void, Error, void>) {
  const queryClient = useQueryClient();
  const { logout: clearAuthStore } = useAuthStore();

  return useMutation({
    mutationFn: authAPI.logout,
    onSuccess: () => {
      clearAuthStore();
      queryClient.clear();
    },
    onError: () => {
      // Even on error, clear local state
      clearAuthStore();
      TokenManager.clearTokens();
      queryClient.clear();
    },
    ...options,
  });
}

export function useChangePassword(
  options?: UseMutationOptions<{ message: string }, Error, { oldPassword: string; newPassword: string; confirmPassword: string }>
) {
  return useMutation({
    mutationFn: ({ oldPassword, newPassword, confirmPassword }) =>
      authAPI.changePassword(oldPassword, newPassword, confirmPassword),
    ...options,
  });
}

export function useForgotPassword(
  options?: UseMutationOptions<{ message: string }, Error, string>
) {
  return useMutation({
    mutationFn: authAPI.forgotPassword,
    ...options,
  });
}

export function useResetPassword(
  options?: UseMutationOptions<{ message: string }, Error, { token: string; newPassword: string }>
) {
  return useMutation({
    mutationFn: ({ token, newPassword }) => authAPI.resetPassword(token, newPassword),
    ...options,
  });
}

export function useResendVerification(
  options?: UseMutationOptions<{ message: string }, Error, string>
) {
  return useMutation({
    mutationFn: authAPI.resendVerification,
    ...options,
  });
}

export function useVerifyEmail(
  options?: UseMutationOptions<{ message: string }, Error, string>
) {
  return useMutation({
    mutationFn: authAPI.verifyEmail,
    ...options,
  });
}

// ============================================================================
// User Hooks
// ============================================================================

export function useCurrentUser(
  options?: Omit<UseQueryOptions<User, Error>, "queryKey" | "queryFn">
) {
  const { setUser, setLoading } = useAuthStore();

  return useQuery({
    queryKey: queryKeys.currentUser,
    queryFn: usersAPI.getCurrentUser,
    staleTime: 5 * 60 * 1000,
    retry: 1,
    enabled: TokenManager.hasTokens(),
    ...options,
  });
}

export function useCurrentUserFull(
  options?: Omit<UseQueryOptions<UserFull, Error>, "queryKey" | "queryFn">
) {
  return useQuery({
    queryKey: queryKeys.currentUserFull,
    queryFn: usersAPI.getCurrentUserFull,
    staleTime: 5 * 60 * 1000,
    retry: 1,
    enabled: TokenManager.hasTokens(),
    ...options,
  });
}

export function useUpdateProfile(
  options?: UseMutationOptions<User, Error, { first_name?: string; last_name?: string; country?: string }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: usersAPI.updateProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.currentUser });
      queryClient.invalidateQueries({ queryKey: queryKeys.currentUserFull });
    },
    ...options,
  });
}

export function useAuditLogs(
  page: number = 1,
  pageSize: number = 20,
  options?: Omit<UseQueryOptions<PaginatedResponse<AuditLog>, Error>, "queryKey" | "queryFn">
) {
  return useQuery({
    queryKey: queryKeys.auditLogs(page),
    queryFn: () => usersAPI.getAuditLogs(page, pageSize),
    staleTime: 60 * 1000,
    ...options,
  });
}

// ============================================================================
// Trader Hooks
// ============================================================================

export function useTraders(
  params?: { page?: number; page_size?: number; sort_by?: string; min_roi?: number },
  options?: Omit<UseQueryOptions<PaginatedResponse<TraderProfile>, Error>, "queryKey" | "queryFn">
) {
  return useQuery({
    queryKey: queryKeys.tradersList(params),
    queryFn: () => tradersAPI.getAll(params),
    staleTime: 2 * 60 * 1000,
    ...options,
  });
}

export function useTrader(
  id: string,
  options?: Omit<UseQueryOptions<TraderProfile, Error>, "queryKey" | "queryFn">
) {
  return useQuery({
    queryKey: queryKeys.trader(id),
    queryFn: () => tradersAPI.getById(id),
    enabled: !!id,
    ...options,
  });
}

export function useTraderTrades(
  id: string,
  page: number = 1,
  pageSize: number = 20,
  options?: Omit<UseQueryOptions<PaginatedResponse<Trade>, Error>, "queryKey" | "queryFn">
) {
  return useQuery({
    queryKey: queryKeys.traderTrades(id, page),
    queryFn: () => tradersAPI.getTrades(id, page, pageSize),
    enabled: !!id,
    ...options,
  });
}

export function useApplyTrader(
  options?: UseMutationOptions<TraderProfile, Error, TraderProfileCreate>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: tradersAPI.apply,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.currentUserFull });
      queryClient.invalidateQueries({ queryKey: queryKeys.myTraderProfile });
    },
    ...options,
  });
}

export function useMyTraderProfile(
  options?: Omit<UseQueryOptions<TraderProfile, Error>, "queryKey" | "queryFn">
) {
  return useQuery({
    queryKey: queryKeys.myTraderProfile,
    queryFn: tradersAPI.getMyProfile,
    staleTime: 5 * 60 * 1000,
    retry: false,
    ...options,
  });
}

export function useSubmitKYC(
  options?: UseMutationOptions<{ message: string }, Error, {
    first_name: string;
    last_name: string;
    country: string;
    date_of_birth?: string;
    past_trades?: string;
    id_document: File;
  }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: tradersAPI.submitKYC,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.currentUserFull });
    },
    ...options,
  });
}

// ============================================================================
// Exchange Keys Hooks
// ============================================================================

export function useExchangeKeys(
  exchange?: string,
  options?: Omit<UseQueryOptions<ExchangeKey[], Error>, "queryKey" | "queryFn">
) {
  return useQuery({
    queryKey: queryKeys.exchangeKeys,
    queryFn: () => keysAPI.getAll(exchange),
    staleTime: 5 * 60 * 1000,
    ...options,
  });
}

export function useCreateExchangeKey(
  options?: UseMutationOptions<ExchangeKey, Error, ExchangeKeyCreate>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: keysAPI.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.exchangeKeys });
    },
    ...options,
  });
}

export function useRevokeExchangeKey(
  options?: UseMutationOptions<void, Error, string>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: keysAPI.revoke,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.exchangeKeys });
    },
    ...options,
  });
}

export function useValidateExchangeKey(
  options?: UseMutationOptions<{ valid: boolean; permissions: string[] }, Error, string>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: keysAPI.validate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.exchangeKeys });
    },
    ...options,
  });
}

// ============================================================================
// Subscription Hooks
// ============================================================================

export function useSubscriptions(
  status?: string,
  options?: Omit<UseQueryOptions<Subscription[], Error>, "queryKey" | "queryFn">
) {
  return useQuery({
    queryKey: queryKeys.subscriptions,
    queryFn: () => subscriptionsAPI.getAll(status),
    staleTime: 30 * 1000,
    ...options,
  });
}

export function useSubscription(
  id: string,
  options?: Omit<UseQueryOptions<Subscription, Error>, "queryKey" | "queryFn">
) {
  return useQuery({
    queryKey: queryKeys.subscription(id),
    queryFn: () => subscriptionsAPI.getById(id),
    enabled: !!id,
    ...options,
  });
}

export function useCreateSubscription(
  options?: UseMutationOptions<Subscription, Error, SubscriptionCreate>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: subscriptionsAPI.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.subscriptions });
      queryClient.invalidateQueries({ queryKey: queryKeys.walletBalance });
    },
    ...options,
  });
}

export function useUpdateSubscription(
  options?: UseMutationOptions<Subscription, Error, { id: string; data: SubscriptionUpdate }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => subscriptionsAPI.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.subscriptions });
    },
    ...options,
  });
}

export function usePauseSubscription(
  options?: UseMutationOptions<Subscription, Error, string>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: subscriptionsAPI.pause,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.subscriptions });
    },
    ...options,
  });
}

export function useResumeSubscription(
  options?: UseMutationOptions<Subscription, Error, string>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: subscriptionsAPI.resume,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.subscriptions });
    },
    ...options,
  });
}

export function useStopSubscription(
  options?: UseMutationOptions<Subscription, Error, string>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: subscriptionsAPI.stop,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.subscriptions });
      queryClient.invalidateQueries({ queryKey: queryKeys.walletBalance });
    },
    ...options,
  });
}

export function usePauseAllSubscriptions(
  options?: UseMutationOptions<{ message: string; paused_count: number }, Error, void>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: subscriptionsAPI.pauseAll,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.subscriptions });
    },
    ...options,
  });
}

export function useSubscriptionTrades(
  id: string,
  page: number = 1,
  pageSize: number = 20,
  options?: Omit<UseQueryOptions<PaginatedResponse<Trade>, Error>, "queryKey" | "queryFn">
) {
  return useQuery({
    queryKey: queryKeys.subscriptionTrades(id, page),
    queryFn: () => subscriptionsAPI.getTrades(id, page, pageSize),
    enabled: !!id,
    ...options,
  });
}

// ============================================================================
// Wallet Hooks
// ============================================================================

export function useWalletBalance(
  options?: Omit<UseQueryOptions<LedgerAccount[], Error>, "queryKey" | "queryFn">
) {
  return useQuery({
    queryKey: queryKeys.walletBalance,
    queryFn: walletAPI.getBalance,
    staleTime: 30 * 1000,
    refetchInterval: 60 * 1000,
    ...options,
  });
}

export function useLedger(
  params?: { page?: number; page_size?: number; transaction_type?: string; start_date?: string; end_date?: string },
  options?: Omit<UseQueryOptions<PaginatedResponse<LedgerEntry>, Error>, "queryKey" | "queryFn">
) {
  return useQuery({
    queryKey: queryKeys.ledger(params),
    queryFn: () => walletAPI.getLedger(params),
    staleTime: 60 * 1000,
    ...options,
  });
}

export function useInitiateDeposit(
  options?: UseMutationOptions<{ payment_url: string; reference: string }, Error, { amount: number; currency: string }>
) {
  return useMutation({
    mutationFn: ({ amount, currency }) => walletAPI.initiateDeposit(amount, currency),
    ...options,
  });
}

export function useRequestWithdrawal(
  options?: UseMutationOptions<{ reference: string; status: string }, Error, { amount: number; currency: string; bank_account_id: string }>
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ amount, currency, bank_account_id }) =>
      walletAPI.requestWithdrawal(amount, currency, bank_account_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.walletBalance });
      queryClient.invalidateQueries({ queryKey: queryKeys.ledger({}) });
    },
    ...options,
  });
}

export function useJoinWaitlist(
  options?: UseMutationOptions<{ message: string }, Error, string>
) {
  return useMutation({
    mutationFn: waitlistAPI.join,
    ...options,
  });
}
