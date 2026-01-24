import { create } from "zustand";
import { persist } from "zustand/middleware";

export type ConnectionStatus = "connected" | "connecting" | "disconnected" | "error";

export interface SystemHealth {
  sentinel: ConnectionStatus;
  exchange: ConnectionStatus;
  wallet: ConnectionStatus;
  lastHeartbeat: number | null;
  executionLatency: number;
  websocketLatency: number;
}

export interface SystemStore {
  health: SystemHealth;
  setHealth: (health: Partial<SystemHealth>) => void;
  setSentinelStatus: (status: ConnectionStatus) => void;
  setExchangeStatus: (status: ConnectionStatus) => void;
  setWalletStatus: (status: ConnectionStatus) => void;
  updateLatency: (executionLatency: number, websocketLatency?: number) => void;
  recordHeartbeat: () => void;
}

export const useSystemStore = create<SystemStore>((set) => ({
  health: {
    sentinel: "disconnected",
    exchange: "disconnected",
    wallet: "disconnected",
    lastHeartbeat: null,
    executionLatency: 0,
    websocketLatency: 0,
  },
  setHealth: (health) =>
    set((state) => ({
      health: { ...state.health, ...health },
    })),
  setSentinelStatus: (status) =>
    set((state) => ({
      health: { ...state.health, sentinel: status },
    })),
  setExchangeStatus: (status) =>
    set((state) => ({
      health: { ...state.health, exchange: status },
    })),
  setWalletStatus: (status) =>
    set((state) => ({
      health: { ...state.health, wallet: status },
    })),
  updateLatency: (executionLatency, websocketLatency) =>
    set((state) => ({
      health: {
        ...state.health,
        executionLatency,
        websocketLatency: websocketLatency ?? state.health.websocketLatency,
      },
    })),
  recordHeartbeat: () =>
    set((state) => ({
      health: { ...state.health, lastHeartbeat: Date.now() },
    })),
}));

/**
 * UI State Store
 * Manages sidebar, modals, and general UI state
 */
export interface UIStore {
  sidebarOpen: boolean;
  sidebarCollapsed: boolean;
  activeModal: string | null;
  commandPaletteOpen: boolean;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  openModal: (modalId: string) => void;
  closeModal: () => void;
  toggleCommandPalette: () => void;
}

export const useUIStore = create<UIStore>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      sidebarCollapsed: false,
      activeModal: null,
      commandPaletteOpen: false,
      toggleSidebar: () =>
        set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setSidebarCollapsed: (collapsed) =>
        set({ sidebarCollapsed: collapsed }),
      openModal: (modalId) => set({ activeModal: modalId }),
      closeModal: () => set({ activeModal: null }),
      toggleCommandPalette: () =>
        set((state) => ({ commandPaletteOpen: !state.commandPaletteOpen })),
    }),
    {
      name: "jars-ui-state",
      partialize: (state) => ({
        sidebarCollapsed: state.sidebarCollapsed,
      }),
    }
  )
);

/**
 * Trading State Store
 * Manages the currently selected trader, active trades, and trading state
 */
export interface Trader {
  id: string;
  name: string;
  username: string;
  avatar: string | null;
  roi30d: number;
  roi90d: number;
  roiTotal: number;
  winRate: number;
  maxDrawdown: number;
  totalTrades: number;
  copiers: number;
  isVerified: boolean;
  isIncubation: boolean;
  joinedAt: string;
  tradingPairs: string[];
  avgTradeSize: number;
  riskLevel: "low" | "medium" | "high";
}

export interface ActiveCopy {
  id: string;
  traderId: string;
  traderName: string;
  startedAt: string;
  allocation: number;
  allocationPercentage: number;
  profitLoss: number;
  profitLossPercentage: number;
  tradesExecuted: number;
  status: "active" | "paused" | "stopped";
}

export interface TradingStore {
  selectedTrader: Trader | null;
  activeCopies: ActiveCopy[];
  isPaused: boolean;
  selectTrader: (trader: Trader | null) => void;
  setActiveCopies: (copies: ActiveCopy[]) => void;
  addActiveCopy: (copy: ActiveCopy) => void;
  removeCopy: (copyId: string) => void;
  pauseAllTrading: () => void;
  resumeAllTrading: () => void;
}

export const useTradingStore = create<TradingStore>((set) => ({
  selectedTrader: null,
  activeCopies: [],
  isPaused: false,
  selectTrader: (trader) => set({ selectedTrader: trader }),
  setActiveCopies: (copies) => set({ activeCopies: copies }),
  addActiveCopy: (copy) =>
    set((state) => ({ activeCopies: [...state.activeCopies, copy] })),
  removeCopy: (copyId) =>
    set((state) => ({
      activeCopies: state.activeCopies.filter((c) => c.id !== copyId),
    })),
  pauseAllTrading: () => set({ isPaused: true }),
  resumeAllTrading: () => set({ isPaused: false }),
}));

/**
 * Notification Store
 * Manages toast notifications and alerts
 */
export type NotificationType = "info" | "success" | "warning" | "error";

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message?: string;
  timestamp: number;
  read: boolean;
  persistent?: boolean;
}

export interface NotificationStore {
  notifications: Notification[];
  unreadCount: number;
  addNotification: (notification: Omit<Notification, "id" | "timestamp" | "read">) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
}

export const useNotificationStore = create<NotificationStore>((set) => ({
  notifications: [],
  unreadCount: 0,
  addNotification: (notification) => {
    const newNotification: Notification = {
      ...notification,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now(),
      read: false,
    };
    set((state) => ({
      notifications: [newNotification, ...state.notifications].slice(0, 50),
      unreadCount: state.unreadCount + 1,
    }));
  },
  markAsRead: (id) =>
    set((state) => {
      const notification = state.notifications.find((n) => n.id === id);
      if (notification && !notification.read) {
        return {
          notifications: state.notifications.map((n) =>
            n.id === id ? { ...n, read: true } : n
          ),
          unreadCount: Math.max(0, state.unreadCount - 1),
        };
      }
      return state;
    }),
  markAllAsRead: () =>
    set((state) => ({
      notifications: state.notifications.map((n) => ({ ...n, read: true })),
      unreadCount: 0,
    })),
  removeNotification: (id) =>
    set((state) => {
      const notification = state.notifications.find((n) => n.id === id);
      return {
        notifications: state.notifications.filter((n) => n.id !== id),
        unreadCount:
          notification && !notification.read
            ? Math.max(0, state.unreadCount - 1)
            : state.unreadCount,
      };
    }),
  clearAll: () => set({ notifications: [], unreadCount: 0 }),
}));

/**
 * User/Auth Store
 * Manages authenticated user state
 */
export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  avatar: string | null;
  is2faEnabled: boolean;
  isKycVerified: boolean;
  kycStatus: "pending" | "verified" | "rejected" | "not_started";
  country: string | null;
  createdAt: string;
}

export interface AuthStore {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setUser: (user: User | null) => void;
  setLoading: (loading: boolean) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  setUser: (user) =>
    set({
      user,
      isAuthenticated: !!user,
      isLoading: false,
    }),
  setLoading: (loading) => set({ isLoading: loading }),
  logout: () =>
    set({
      user: null,
      isAuthenticated: false,
      isLoading: false,
    }),
}));

