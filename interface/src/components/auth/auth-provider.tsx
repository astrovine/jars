"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useRouter, usePathname } from "next/navigation";
import { usersAPI, TokenManager } from "@/lib/api";
import type { User as APIUser } from "@/types";

interface AuthContextType {
  user: APIUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Routes that don't require authentication
const PUBLIC_ROUTES = [
  "/",
  "/login",
  "/register",
  "/forgot-password",
  "/reset-password",
  "/verify-email",
  "/terms",
  "/privacy",
  "/waitlist",
];

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  const [user, setUser] = useState<APIUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const isPublicRoute = PUBLIC_ROUTES.some(route => pathname === route || pathname.startsWith("/verify-email"));

  const fetchUser = useCallback(async () => {
    if (!TokenManager.hasTokens()) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const userData = await usersAPI.getCurrentUser();
      setUser(userData);
    } catch (err) {
      console.error("[Auth] Failed to fetch user:", err);
      setError(err as Error);
      setUser(null);

      // Clear tokens on auth error
      if ((err as any)?.status === 401) {
        TokenManager.clearTokens();
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    TokenManager.clearTokens();
    setUser(null);
    router.push("/login");
  }, [router]);

  // Initial auth check
  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  // Redirect logic
  useEffect(() => {
    if (isLoading) return;

    const hasToken = TokenManager.hasTokens();

    if (!hasToken && !isPublicRoute) {
      // Not authenticated and trying to access protected route
      router.push("/login");
    }
  }, [isLoading, user, isPublicRoute, router, pathname]);

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    error,
    refetch: fetchUser,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

/**
 * Hook to protect routes - redirects to login if not authenticated
 */
export function useRequireAuth() {
  const { user, isLoading, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  return { user, isLoading, isAuthenticated };
}

