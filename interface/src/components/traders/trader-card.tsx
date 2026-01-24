"use client";

import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn, formatCurrency, formatPercentage } from "@/lib/utils";
import type { TraderProfile } from "@/types";
import {
  TrendingUp,
  TrendingDown,
  Users,
  Award,
  Star,
} from "lucide-react";

interface TraderCardProps {
  trader: TraderProfile;
  onCopy?: () => void;
  onSelect?: () => void;
}

export function TraderCard({ trader, onCopy, onSelect }: TraderCardProps) {
  const isVerified = trader.status === "ACTIVE";
  const isIncubation = trader.status === "INCUBATION";
  const isProfitable = trader.total_pnl >= 0;

  return (
    <Card
      className="bg-[#111111] border-[#1a1a1a] hover:border-[#262626] transition-colors cursor-pointer"
      onClick={onSelect}
    >
      <CardContent className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#3B82F6] to-[#1D4ED8] flex items-center justify-center text-white font-bold text-lg">
              {trader.alias.charAt(0).toUpperCase()}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-[#ededed]">{trader.alias}</h3>
                {isVerified && (
                  <Badge variant="success" className="text-[9px]">
                    Verified
                  </Badge>
                )}
                {isIncubation && (
                  <Badge variant="warning" className="text-[9px]">
                    Incubation
                  </Badge>
                )}
              </div>
              <p className="text-xs text-[#737373]">
                {trader.current_subscribers} copiers
              </p>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="text-center p-2 rounded-lg bg-[#0A0A0A]">
            <p className="text-[10px] text-[#737373] mb-1">Win Rate</p>
            <p className="font-mono text-sm font-medium text-[#ededed]">
              {formatPercentage(trader.win_rate, 1, false)}
            </p>
          </div>
          <div className="text-center p-2 rounded-lg bg-[#0A0A0A]">
            <p className="text-[10px] text-[#737373] mb-1">Total P&L</p>
            <p className={cn(
              "font-mono text-sm font-medium",
              isProfitable ? "text-[#22C55E]" : "text-[#EF4444]"
            )}>
              {formatCurrency(trader.total_pnl, "NGN")}
            </p>
          </div>
          <div className="text-center p-2 rounded-lg bg-[#0A0A0A]">
            <p className="text-[10px] text-[#737373] mb-1">Trades</p>
            <p className="font-mono text-sm font-medium text-[#ededed]">
              {trader.total_trades}
            </p>
          </div>
        </div>

        {/* Fee & Min */}
        <div className="flex items-center justify-between text-xs text-[#737373] mb-4">
          <span>Fee: {trader.performance_fee_percentage}%</span>
          <span>Min: {formatCurrency(trader.min_allocation_amount, "NGN")}</span>
        </div>

        {/* Action */}
        <Button
          className="w-full bg-[#3B82F6] hover:bg-[#2563EB]"
          disabled={!isVerified}
          onClick={(e) => {
            e.stopPropagation();
            onCopy?.();
          }}
        >
          <TrendingUp className="w-4 h-4 mr-2" />
          Copy Trader
        </Button>
      </CardContent>
    </Card>
  );
}

