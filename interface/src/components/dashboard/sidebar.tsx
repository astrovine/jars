"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/lib/stores";
import {
  LayoutDashboard,
  Users,
  History,
  BookOpen,
  Settings,
  Key,
  ShieldCheck,
  HelpCircle,
  ChevronLeft,
  ChevronRight,
  TrendingUp,
  Wallet,
  Bell,
  BarChart3,
  AlertOctagon,
} from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  badge?: string | number;
  badgeVariant?: "default" | "warning" | "danger";
}

interface NavSection {
  title?: string;
  items: NavItem[];
}

const navigation: NavSection[] = [
  {
    items: [
      { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
      { label: "Portfolio", href: "/dashboard/portfolio", icon: TrendingUp },
      { label: "Traders", href: "/dashboard/traders", icon: Users },
    ],
  },
  {
    title: "Trading",
    items: [
      { label: "Active Copies", href: "/dashboard/copies", icon: BarChart3 },
      { label: "Trade History", href: "/dashboard/history", icon: History },
      { label: "Wallet", href: "/dashboard/wallet", icon: Wallet },
      { label: "Ledger", href: "/dashboard/ledger", icon: BookOpen },
    ],
  },
  {
    title: "Settings",
    items: [
      { label: "API Keys", href: "/dashboard/keys", icon: Key },
      { label: "Notifications", href: "/dashboard/notifications", icon: Bell },
      { label: "Security", href: "/dashboard/security", icon: ShieldCheck },
      { label: "Preferences", href: "/dashboard/settings", icon: Settings },
    ],
  },
];

const NavLink: React.FC<{
  item: NavItem;
  collapsed: boolean;
  isActive: boolean;
}> = ({ item, collapsed, isActive }) => {
  const content = (
    <Link
      href={item.href}
      className={cn(
        "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150",
        isActive
          ? "bg-[var(--primary-subtle)] text-[var(--primary)] border border-[var(--primary)]/20"
          : "text-[var(--foreground-muted)] hover:text-[var(--foreground)] hover:bg-[var(--background-surface)]",
        collapsed && "justify-center px-2"
      )}
    >
      <item.icon
        className={cn(
          "w-5 h-5 flex-shrink-0",
          isActive ? "text-[var(--primary)]" : ""
        )}
      />
      {!collapsed && (
        <>
          <span className="flex-1">{item.label}</span>
          {item.badge !== undefined && (
            <span
              className={cn(
                "px-1.5 py-0.5 rounded text-[10px] font-semibold tabular-nums",
                item.badgeVariant === "danger"
                  ? "bg-[var(--danger-subtle)] text-[var(--danger-text)]"
                  : item.badgeVariant === "warning"
                  ? "bg-[var(--warning-subtle)] text-[var(--warning-text)]"
                  : "bg-[var(--background-muted)] text-[var(--foreground-muted)]"
              )}
            >
              {item.badge}
            </span>
          )}
        </>
      )}
    </Link>
  );

  if (collapsed) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>{content}</TooltipTrigger>
        <TooltipContent side="right" className="flex items-center gap-2">
          {item.label}
          {item.badge !== undefined && (
            <span className="text-[var(--foreground-subtle)]">
              ({item.badge})
            </span>
          )}
        </TooltipContent>
      </Tooltip>
    );
  }

  return content;
};

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const { sidebarCollapsed, setSidebarCollapsed } = useUIStore();

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 h-screen bg-[var(--background-elevated)] border-r border-[var(--border)] flex flex-col transition-all duration-200 z-[var(--z-sticky)]",
        sidebarCollapsed ? "w-[72px]" : "w-[240px]"
      )}
    >
      {/* Logo */}
      <div
        className={cn(
          "flex items-center h-14 border-b border-[var(--border)] px-4",
          sidebarCollapsed && "justify-center px-2"
        )}
      >
        <Link href="/dashboard" className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--primary)] to-[var(--primary-muted)] flex items-center justify-center">
            <span className="text-white font-bold text-sm">J</span>
          </div>
          {!sidebarCollapsed && (
            <span className="text-lg font-semibold text-[var(--foreground)] tracking-tight">
              JARS
            </span>
          )}
        </Link>
      </div>

      {/* Navigation */}
      <ScrollArea className="flex-1 px-3 py-4">
        <nav className="space-y-6">
          {navigation.map((section, sectionIndex) => (
            <div key={sectionIndex}>
              {section.title && !sidebarCollapsed && (
                <h3 className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-wider text-[var(--foreground-subtle)]">
                  {section.title}
                </h3>
              )}
              {section.title && sidebarCollapsed && (
                <Separator className="my-2" />
              )}
              <div className="space-y-1">
                {section.items.map((item) => (
                  <NavLink
                    key={item.href}
                    item={item}
                    collapsed={sidebarCollapsed}
                    isActive={pathname === item.href}
                  />
                ))}
              </div>
            </div>
          ))}
        </nav>
      </ScrollArea>

      {/* Emergency Kill Switch */}
      <div className="p-3 border-t border-[var(--border)]">
        {sidebarCollapsed ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="danger"
                size="icon"
                className="w-full"
                aria-label="Emergency Stop"
              >
                <AlertOctagon className="w-5 h-5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right">
              <span className="text-[var(--danger)]">
                Emergency: Pause All Trading
              </span>
            </TooltipContent>
          </Tooltip>
        ) : (
          <Button
            variant="danger"
            size="sm"
            className="w-full justify-start gap-2"
          >
            <AlertOctagon className="w-4 h-4" />
            <span>Pause All Trading</span>
          </Button>
        )}
      </div>

      {/* Help & Collapse */}
      <div className="p-3 border-t border-[var(--border)] space-y-2">
        {!sidebarCollapsed && (
          <Link
            href="/dashboard/help"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-[var(--foreground-muted)] hover:text-[var(--foreground)] hover:bg-[var(--background-surface)] transition-colors"
          >
            <HelpCircle className="w-5 h-5" />
            <span>Help & Support</span>
          </Link>
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className={cn("w-full", sidebarCollapsed ? "justify-center" : "")}
          aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {sidebarCollapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <>
              <ChevronLeft className="w-4 h-4" />
              <span className="ml-2">Collapse</span>
            </>
          )}
        </Button>
      </div>
    </aside>
  );
};

export default Sidebar;

