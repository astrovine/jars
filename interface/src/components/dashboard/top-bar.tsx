"use client";

import React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/auth/auth-provider";
import { useNotificationStore } from "@/lib/stores";
import { useLogout } from "@/hooks/use-queries";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Badge } from "@/components/ui/badge";
import {
  Bell,
  Search,
  Command,
  User,
  LogOut,
  Settings,
  Shield,
  CreditCard,
  Wallet,
  History,
  AlertCircle,
  CheckCircle,
  Info,
  AlertTriangle,
} from "lucide-react";
import { cn } from "@/lib/utils";

export const TopBar: React.FC = () => {
  const router = useRouter();
  const { user, logout: authLogout } = useAuth();
  const { unreadCount, notifications, markAllAsRead } = useNotificationStore();
  const { mutate: apiLogout, isPending: isLoggingOut } = useLogout({
    onSuccess: () => {
      router.push("/login");
    },
  });

  const getInitials = (firstName?: string, lastName?: string): string => {
    if (!firstName || !lastName) return "?";
    return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();
  };

  const handleLogout = () => {
    apiLogout();
    authLogout();
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case "success":
        return <CheckCircle className="w-4 h-4 text-[#22C55E]" />;
      case "error":
        return <AlertCircle className="w-4 h-4 text-[#EF4444]" />;
      case "warning":
        return <AlertTriangle className="w-4 h-4 text-[#D4A574]" />;
      default:
        return <Info className="w-4 h-4 text-[#3B82F6]" />;
    }
  };

  return (
    <header className="h-14 border-b border-[#1a1a1a] bg-[#111111] flex items-center justify-between px-6">
      {/* Left: Search */}
      <div className="flex items-center gap-4 flex-1">
        <button
          className="flex items-center gap-3 px-3 py-2 rounded-lg bg-[#0A0A0A] border border-[#1a1a1a] text-[#737373] hover:border-[#262626] hover:text-[#a1a1a1] transition-colors w-full max-w-md"
          onClick={() => {
            // TODO: Open command palette
          }}
        >
          <Search className="w-4 h-4" />
          <span className="text-sm">Search traders, trades, settings...</span>
          <div className="ml-auto flex items-center gap-1 text-xs text-[#525252]">
            <Command className="w-3 h-3" />
            <span>K</span>
          </div>
        </button>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2">
        {/* Notifications */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="relative text-[#737373] hover:text-[#ededed] hover:bg-[#1a1a1a]">
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-[#EF4444] text-white text-[10px] font-bold flex items-center justify-center">
                  {unreadCount > 9 ? "9+" : unreadCount}
                </span>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80 bg-[#111111] border-[#1a1a1a]">
            <DropdownMenuLabel className="flex items-center justify-between text-[#ededed]">
              <span>Notifications</span>
              {unreadCount > 0 && (
                <button
                  onClick={() => markAllAsRead()}
                  className="text-xs text-[#3B82F6] hover:underline"
                >
                  Mark all read
                </button>
              )}
            </DropdownMenuLabel>
            <DropdownMenuSeparator className="bg-[#1a1a1a]" />
            {notifications.length === 0 ? (
              <div className="py-8 text-center text-[#737373] text-sm">
                No notifications
              </div>
            ) : (
              <div className="max-h-[400px] overflow-y-auto">
                {notifications.slice(0, 5).map((notification) => (
                  <DropdownMenuItem
                    key={notification.id}
                    className={cn(
                      "flex flex-col items-start gap-1 py-3 focus:bg-[#1a1a1a]",
                      !notification.read && "bg-[#3B82F6]/5"
                    )}
                  >
                    <div className="flex items-start gap-2 w-full">
                      {getNotificationIcon(notification.type)}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-[#ededed] truncate">
                          {notification.title}
                        </p>
                        {notification.message && (
                          <p className="text-xs text-[#737373] line-clamp-2">
                            {notification.message}
                          </p>
                        )}
                        <p className="text-[10px] text-[#525252] mt-1">
                          {new Date(notification.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  </DropdownMenuItem>
                ))}
              </div>
            )}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className="flex items-center gap-2 px-2 hover:bg-[#1a1a1a]"
            >
              <Avatar className="w-8 h-8 border border-[#262626]">
                <AvatarFallback className="bg-gradient-to-br from-[#3B82F6] to-[#1D4ED8] text-white text-sm">
                  {getInitials(user?.first_name, user?.last_name)}
                </AvatarFallback>
              </Avatar>
              <div className="hidden md:flex flex-col items-start">
                <span className="text-sm font-medium text-[#ededed]">
                  {user?.first_name} {user?.last_name}
                </span>
                <span className="text-[10px] text-[#737373]">
                  {user?.email}
                </span>
              </div>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56 bg-[#111111] border-[#1a1a1a]">
            <DropdownMenuLabel className="text-[#ededed]">
              <div className="flex flex-col gap-1">
                <span>{user?.first_name} {user?.last_name}</span>
                <span className="text-xs font-normal text-[#737373]">
                  {user?.email}
                </span>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator className="bg-[#1a1a1a]" />
            <DropdownMenuGroup>
              <DropdownMenuItem asChild className="text-[#a1a1a1] focus:bg-[#1a1a1a] focus:text-[#ededed]">
                <Link href="/dashboard" className="flex items-center gap-2">
                  <User className="w-4 h-4" />
                  <span>Dashboard</span>
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild className="text-[#a1a1a1] focus:bg-[#1a1a1a] focus:text-[#ededed]">
                <Link href="/dashboard/wallet" className="flex items-center gap-2">
                  <Wallet className="w-4 h-4" />
                  <span>Wallet</span>
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild className="text-[#a1a1a1] focus:bg-[#1a1a1a] focus:text-[#ededed]">
                <Link href="/dashboard/history" className="flex items-center gap-2">
                  <History className="w-4 h-4" />
                  <span>Trade History</span>
                </Link>
              </DropdownMenuItem>
            </DropdownMenuGroup>
            <DropdownMenuSeparator className="bg-[#1a1a1a]" />
            <DropdownMenuGroup>
              <DropdownMenuItem asChild className="text-[#a1a1a1] focus:bg-[#1a1a1a] focus:text-[#ededed]">
                <Link href="/dashboard/settings" className="flex items-center gap-2">
                  <Settings className="w-4 h-4" />
                  <span>Settings</span>
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild className="text-[#a1a1a1] focus:bg-[#1a1a1a] focus:text-[#ededed]">
                <Link href="/dashboard/security" className="flex items-center gap-2">
                  <Shield className="w-4 h-4" />
                  <span>Security</span>
                </Link>
              </DropdownMenuItem>
            </DropdownMenuGroup>
            <DropdownMenuSeparator className="bg-[#1a1a1a]" />
            <DropdownMenuItem
              onClick={handleLogout}
              disabled={isLoggingOut}
              className="text-[#EF4444] focus:bg-[#EF4444]/10 focus:text-[#EF4444]"
            >
              <LogOut className="w-4 h-4 mr-2" />
              <span>{isLoggingOut ? "Logging out..." : "Log out"}</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
};

