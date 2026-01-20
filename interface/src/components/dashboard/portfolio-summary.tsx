"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn, formatCurrency, formatPercentage, formatCompactNumber } from "@/lib/utils";
import {
  TrendingUp,
  TrendingDown,
  Wallet,
  Activity,
  Users,
  BarChart3,
  Clock,
  Info,
} from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string;
  change?: number;
  changeLabel?: string;
  icon: React.ReactNode;
  tooltip?: string;
  trend?: "up" | "down" | "neutral";
  loading?: boolean;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  change,
  changeLabel,
  icon,
  tooltip,
  trend,
  loading = false,
}) => {
  const getTrendColor = () => {
    if (trend === "up") return "text-[var(--profit)]";
    if (trend === "down") return "text-[var(--loss)]";
    return "text-[var(--foreground-muted)]";
  };

  const getTrendIcon = () => {
    if (trend === "up")
      return <TrendingUp className="w-3.5 h-3.5 text-[var(--profit)]" />;
    if (trend === "down")
      return <TrendingDown className="w-3.5 h-3.5 text-[var(--loss)]" />;
    return null;
  };

  if (loading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <div className="skeleton h-4 w-24" />
        </CardHeader>
        <CardContent>
          <div className="skeleton h-8 w-32 mb-2" />
          <div className="skeleton h-3 w-20" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="relative overflow-hidden">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-[var(--foreground-muted)] flex items-center gap-2">
            {icon}
            <span>{title}</span>
            {tooltip && (
              <Tooltip>
                <TooltipTrigger>
                  <Info className="w-3.5 h-3.5 text-[var(--foreground-subtle)]" />
                </TooltipTrigger>
                <TooltipContent>
                  <p className="max-w-xs">{tooltip}</p>
                </TooltipContent>
              </Tooltip>
            )}
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="font-mono text-2xl font-semibold text-[var(--foreground)] tabular-nums">
          {value}
        </div>
        {change !== undefined && (
          <div className="flex items-center gap-1 mt-1">
            {getTrendIcon()}
            <span className={cn("text-sm font-mono tabular-nums", getTrendColor())}>
              {formatPercentage(change)}
            </span>
            {changeLabel && (
              <span className="text-xs text-[var(--foreground-subtle)]">
                {changeLabel}
              </span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

interface PortfolioSummaryProps {
  totalBalance: number;
  availableBalance: number;
  totalPnl: number;
  totalPnlPercentage: number;
  todayPnl: number;
  todayPnlPercentage: number;
  activeCopies: number;
  totalTradesCopied: number;
  avgLatency: number;
  loading?: boolean;
}

export const PortfolioSummary: React.FC<PortfolioSummaryProps> = ({
  totalBalance,
  availableBalance,
  totalPnl,
  totalPnlPercentage,
  todayPnl,
  todayPnlPercentage,
  activeCopies,
  totalTradesCopied,
  avgLatency,
  loading = false,
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-4">
      <MetricCard
        title="Total Balance"
        value={formatCurrency(totalBalance)}
        icon={<Wallet className="w-4 h-4" />}
        tooltip="Total value across all trading accounts"
        loading={loading}
      />
      <MetricCard
        title="Available"
        value={formatCurrency(availableBalance)}
        icon={<BarChart3 className="w-4 h-4" />}
        tooltip="Balance available for new copy trading allocations"
        loading={loading}
      />
      <MetricCard
        title="Total P&L"
        value={formatCurrency(totalPnl)}
        change={totalPnlPercentage}
        changeLabel="all time"
        icon={<Activity className="w-4 h-4" />}
        trend={totalPnl >= 0 ? "up" : "down"}
        tooltip="Cumulative profit/loss from all copy trading activity"
        loading={loading}
      />
      <MetricCard
        title="Today's P&L"
        value={formatCurrency(todayPnl)}
        change={todayPnlPercentage}
        changeLabel="24h"
        icon={<TrendingUp className="w-4 h-4" />}
        trend={todayPnl >= 0 ? "up" : "down"}
        tooltip="Profit/loss in the last 24 hours"
        loading={loading}
      />
      <MetricCard
        title="Active Copies"
        value={activeCopies.toString()}
        icon={<Users className="w-4 h-4" />}
        tooltip={`Copying ${activeCopies} traders | ${formatCompactNumber(totalTradesCopied)} trades executed`}
        loading={loading}
      />
    </div>
  );
};

interface LatencyIndicatorProps {
  latency: number;
  label: string;
}

export const LatencyIndicator: React.FC<LatencyIndicatorProps> = ({
  latency,
  label,
}) => {
  const getLatencyStatus = () => {
    if (latency < 50) return { color: "bg-[var(--success)]", text: "Excellent" };
    if (latency < 150) return { color: "bg-[var(--success)]", text: "Good" };
    if (latency < 500) return { color: "bg-[var(--warning)]", text: "Moderate" };
    return { color: "bg-[var(--danger)]", text: "High" };
  };

  const status = getLatencyStatus();

  return (
    <div className="flex items-center gap-3 p-3 rounded-lg bg-[var(--background-surface)] border border-[var(--border)]">
      <Clock className="w-4 h-4 text-[var(--foreground-muted)]" />
      <div className="flex-1">
        <p className="text-xs text-[var(--foreground-muted)]">{label}</p>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="font-mono text-lg font-semibold tabular-nums text-[var(--foreground)]">
            {latency}ms
          </span>
          <div className="flex items-center gap-1">
            <div className={cn("w-2 h-2 rounded-full", status.color)} />
            <span className="text-xs text-[var(--foreground-muted)]">
              {status.text}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioSummary;

