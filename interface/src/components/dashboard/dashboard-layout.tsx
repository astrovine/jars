"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn, formatCurrency } from "@/lib/utils";
import { useAuth } from "@/components/auth/auth-provider";
import { useWalletBalance } from "@/hooks/use-queries";
import { Button } from "@/components/ui/button";
import {
  LayoutDashboard,
  Users,
  Wallet,
  Key,
  History,
  Settings,
  Shield,
  BookOpen,
  PieChart,
  Menu,
  X,
  LogOut,
  ChevronDown,
  Bell,
  Zap,
} from "lucide-react";


interface DashboardLayoutProps {
  children: React.ReactNode;
}

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Traders", href: "/dashboard/traders", icon: Users },
  { name: "My Copies", href: "/dashboard/copies", icon: PieChart },
  { name: "Portfolio", href: "/dashboard/portfolio", icon: PieChart },
  { name: "Wallet", href: "/dashboard/wallet", icon: Wallet },
  { name: "Ledger", href: "/dashboard/ledger", icon: BookOpen },
  { name: "History", href: "/dashboard/history", icon: History },
  { name: "API Keys", href: "/dashboard/keys", icon: Key },
  { name: "Security", href: "/dashboard/security", icon: Shield },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
];

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Fetch wallet balance
  const { data: balanceData } = useWalletBalance();
  const totalBalance = balanceData?.reduce((sum, acc) => sum + (acc.balance || 0), 0) || 0;

  return (
    <div className="min-h-screen bg-[#09090B]">
      {/* Top Status Bar */}
      <div className="fixed top-0 left-0 right-0 z-50 h-10 bg-[#0A0A0C] border-b border-[#27272A] flex items-center justify-between px-4">
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-[#22C55E] animate-pulse" />
            <span className="text-[#71717A]">Sentinel:</span>
            <span className="text-[#22C55E] font-mono">Connected</span>
          </div>
          <div className="hidden sm:flex items-center gap-2">
            <Zap className="w-3 h-3 text-[#D4A574]" />
            <span className="text-[#71717A]">Latency:</span>
            <span className="text-[#FAFAFA] font-mono">12ms</span>
          </div>
        </div>
        <div className="flex items-center gap-4 text-xs">
          {/* Wallet Balance */}
          <Link
            href="/dashboard/wallet"
            className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#18181B] border border-[#27272A] hover:border-[#3F3F46] transition-colors"
          >
            <Wallet className="w-3.5 h-3.5 text-[#22C55E]" />
            <span className="font-mono text-[#FAFAFA]">{formatCurrency(totalBalance, "NGN")}</span>
          </Link>
          <span className="text-[#52525B]">
            Last sync: <span className="text-[#71717A]">2s ago</span>
          </span>
        </div>
      </div>

      {/* Mobile Header */}
      <div className="lg:hidden fixed top-10 left-0 right-0 z-40 h-14 bg-[#09090B] border-b border-[#27272A] flex items-center justify-between px-4">
        <button
          onClick={() => setSidebarOpen(true)}
          className="p-2 text-[#71717A] hover:text-[#FAFAFA]"
        >
          <Menu className="w-6 h-6" />
        </button>
        <Link href="/">
          <span className="text-xl font-light italic text-[#FAFAFA]">jars</span>
        </Link>
        <button className="p-2 text-[#71717A] hover:text-[#FAFAFA]">
          <Bell className="w-5 h-5" />
        </button>
      </div>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 z-50 bg-black/80"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={cn(
        "fixed top-10 left-0 bottom-0 z-50 w-64 bg-[#0A0A0C] border-r border-[#27272A] transition-transform duration-300",
        "lg:translate-x-0",
        sidebarOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        {/* Logo */}
        <div className="h-14 flex items-center justify-between px-5 border-b border-[#27272A]">
          <Link href="/">
            <span className="text-xl font-light italic text-[#FAFAFA]">jars</span>
          </Link>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-1 text-[#71717A] hover:text-[#FAFAFA]"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-3 space-y-1 flex-1 overflow-y-auto">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={() => setSidebarOpen(false)}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-colors",
                  isActive
                    ? "bg-[#27272A] text-[#FAFAFA]"
                    : "text-[#71717A] hover:text-[#FAFAFA] hover:bg-[#18181B]"
                )}
              >
                <item.icon className={cn(
                  "w-5 h-5",
                  isActive ? "text-[#D4A574]" : ""
                )} />
                {item.name}
              </Link>
            );
          })}
        </nav>

        {/* User Section */}
        <div className="p-4 border-t border-[#27272A]">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#3F3F46] to-[#27272A] flex items-center justify-center text-sm font-medium text-[#FAFAFA]">
              {user?.first_name?.charAt(0) || "U"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-[#FAFAFA] truncate">
                {user?.first_name} {user?.last_name}
              </p>
              <p className="text-xs text-[#52525B] truncate">
                {user?.email}
              </p>
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-sm text-[#71717A] hover:text-[#FAFAFA] hover:bg-[#18181B] transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className={cn(
        "pt-10 lg:pl-64 min-h-screen",
        "pt-24 lg:pt-10" // Extra padding on mobile for header
      )}>
        <div className="p-6 lg:p-8">
          {children}
        </div>
      </main>
    </div>
  );
}

