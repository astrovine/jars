"use client";

import React from "react";
import { cn, formatCurrency } from "@/lib/utils";
import type { LedgerEntry, TransactionType } from "@/types";
import {
  ArrowDownRight,
  ArrowUpRight,
  RefreshCw,
  Download,
  Clock,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

interface LedgerViewProps {
  entries: LedgerEntry[];
  currentBalance?: number;
  loading?: boolean;
  onRefresh?: () => void;
  onExport?: () => void;
}

const transactionTypeConfig: Record<string, { label: string; color: string; icon: React.ElementType }> = {
  DEPOSIT: {
    label: "Deposit",
    color: "text-[#22C55E]",
    icon: ArrowDownRight,
  },
  WITHDRAWAL: {
    label: "Withdrawal",
    color: "text-[#EF4444]",
    icon: ArrowUpRight,
  },
  TRADE_PNL: {
    label: "Trade P&L",
    color: "text-[#3B82F6]",
    icon: RefreshCw,
  },
  FEE: {
    label: "Fee",
    color: "text-[#D4A574]",
    icon: ArrowUpRight,
  },
  PROFIT_SHARE: {
    label: "Profit Share",
    color: "text-[#D4A574]",
    icon: ArrowUpRight,
  },
  REFERRAL: {
    label: "Referral Bonus",
    color: "text-[#22C55E]",
    icon: ArrowDownRight,
  },
  ADJUSTMENT: {
    label: "Adjustment",
    color: "text-[#737373]",
    icon: RefreshCw,
  },
};

export function LedgerView({
  entries,
  currentBalance = 0,
  loading = false,
  onRefresh,
  onExport,
}: LedgerViewProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <Skeleton key={i} className="h-16 w-full bg-[#262626] rounded-lg" />
        ))}
      </div>
    );
  }

  if (entries.length === 0) {
    return (
      <div className="text-center py-12">
        <Clock className="w-12 h-12 text-[#525252] mx-auto mb-3" />
        <p className="text-[#737373]">No transactions found</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {entries.map((entry) => {
        const config = transactionTypeConfig[entry.transaction_type] || transactionTypeConfig.ADJUSTMENT;
        const Icon = config.icon;
        const isCredit = entry.amount > 0;

        return (
          <div
            key={entry.id}
            className="flex items-center justify-between p-4 rounded-lg bg-[#0A0A0A] border border-[#1a1a1a] hover:border-[#262626] transition-colors"
          >
            <div className="flex items-center gap-4">
              <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center bg-opacity-10",
                isCredit ? "bg-[#22C55E]" : "bg-[#EF4444]"
              )}>
                <Icon className={cn("w-5 h-5", config.color)} />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <p className="font-medium text-[#ededed]">{config.label}</p>
                </div>
                <p className="text-xs text-[#737373] mt-0.5">
                  {entry.description || "No description"}
                </p>
                <p className="text-[10px] text-[#525252] mt-1">
                  {new Date(entry.created_at).toLocaleString()}
                </p>
              </div>
            </div>

            <div className="text-right">
              <p className={cn(
                "font-mono font-bold",
                isCredit ? "text-[#22C55E]" : "text-[#EF4444]"
              )}>
                {isCredit ? "+" : ""}{formatCurrency(entry.amount, entry.currency)}
              </p>
              <p className="text-xs text-[#737373] mt-1">
                Balance: {formatCurrency(entry.balance_after, entry.currency)}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

