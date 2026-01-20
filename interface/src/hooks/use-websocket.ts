"use client";

/**
 * WebSocket Hook - Disabled for now
 * Real-time connection will be enabled once the backend WebSocket endpoint is ready
 * Currently using REST API health check instead
 */

import { useCallback, useState } from "react";
import { useSystemStore } from "@/lib/stores";

export interface UseJarsWebSocketOptions {
  onTradeSignal?: (signal: unknown) => void;
  onTradeExecuted?: (trade: unknown) => void;
  onBalanceUpdate?: (balance: unknown) => void;
  onPriceUpdate?: (price: unknown) => void;
  autoConnect?: boolean;
}

export function useJarsWebSocket(options: UseJarsWebSocketOptions = {}) {
  const [isConnected] = useState(false);
  const [latency] = useState(0);

  const subscribe = useCallback((channels: string[]) => {
    // WebSocket disabled - using REST API
    console.debug("[WS] Subscribe requested (disabled):", channels);
  }, []);

  const unsubscribe = useCallback((channels: string[]) => {
    // WebSocket disabled - using REST API
    console.debug("[WS] Unsubscribe requested (disabled):", channels);
  }, []);

  const sendMessage = useCallback((message: string) => {
    // WebSocket disabled - using REST API
    console.debug("[WS] Send requested (disabled):", message);
  }, []);

  return {
    isConnected,
    readyState: 3, // CLOSED
    latency,
    subscribe,
    unsubscribe,
    sendMessage,
  };
}

export const connectionStateMap = {
  0: "connecting",
  1: "connected",
  2: "disconnected",
  3: "disconnected",
} as const;

