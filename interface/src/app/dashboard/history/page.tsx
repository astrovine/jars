"use client";

import React, { useState } from "react";
import { DashboardLayout } from "@/components/dashboard/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useSubscriptions } from "@/hooks/use-queries";
import { cn, formatCurrency } from "@/lib/utils";
import {
  History,
  TrendingUp,
  TrendingDown,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw,
  Download,
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

export default function HistoryPage() {
  const [page, setPage] = useState(1);
  const { data: subscriptions, isLoading, refetch } = useSubscriptions();

  // For now, show subscription-based trade summary since we don't have a dedicated trade history endpoint
  const activeSubscriptions = subscriptions || [];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-[#ededed]">Trade History</h1>
            <p className="text-sm text-[#737373] mt-1">
              View all executed trades across your subscriptions
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              onClick={() => refetch()}
              className="border-[#262626] text-[#a1a1a1]"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
            <Button variant="outline" className="border-[#262626] text-[#a1a1a1]">
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-[#111111] border-[#1a1a1a]">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-[#737373]">Total Trades</p>
                  {isLoading ? (
                    <Skeleton className="h-8 w-20 bg-[#262626] mt-1" />
                  ) : (
                    <p className="text-2xl font-bold font-mono text-[#ededed]">
                      {activeSubscriptions.reduce((sum, s) => sum + (s.total_copied_trades || 0), 0)}
                    </p>
                  )}
                </div>
                <div className="w-10 h-10 rounded-lg bg-[#3B82F6]/10 flex items-center justify-center">
                  <History className="w-5 h-5 text-[#3B82F6]" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-[#111111] border-[#1a1a1a]">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-[#737373]">Active Copies</p>
                  {isLoading ? (
                    <Skeleton className="h-8 w-12 bg-[#262626] mt-1" />
                  ) : (
                    <p className="text-2xl font-bold font-mono text-[#ededed]">
                      {activeSubscriptions.filter(s => s.status === "ACTIVE").length}
                    </p>
                  )}
                </div>
                <div className="w-10 h-10 rounded-lg bg-[#22C55E]/10 flex items-center justify-center">
                  <CheckCircle className="w-5 h-5 text-[#22C55E]" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-[#111111] border-[#1a1a1a]">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-[#737373]">Total Profit</p>
                  {isLoading ? (
                    <Skeleton className="h-8 w-24 bg-[#262626] mt-1" />
                  ) : (
                    <p className="text-2xl font-bold font-mono text-[#22C55E]">
                      {formatCurrency(
                        activeSubscriptions
                          .filter(s => (s.total_pnl || 0) > 0)
                          .reduce((sum, s) => sum + (s.total_pnl || 0), 0),
                        "NGN"
                      )}
                    </p>
                  )}
                </div>
                <div className="w-10 h-10 rounded-lg bg-[#22C55E]/10 flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-[#22C55E]" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-[#111111] border-[#1a1a1a]">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-[#737373]">Total Loss</p>
                  {isLoading ? (
                    <Skeleton className="h-8 w-24 bg-[#262626] mt-1" />
                  ) : (
                    <p className="text-2xl font-bold font-mono text-[#EF4444]">
                      {formatCurrency(
                        Math.abs(
                          activeSubscriptions
                            .filter(s => (s.total_pnl || 0) < 0)
                            .reduce((sum, s) => sum + (s.total_pnl || 0), 0)
                        ),
                        "NGN"
                      )}
                    </p>
                  )}
                </div>
                <div className="w-10 h-10 rounded-lg bg-[#EF4444]/10 flex items-center justify-center">
                  <TrendingDown className="w-5 h-5 text-[#EF4444]" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Subscription Trade Summary */}
        <Card className="bg-[#111111] border-[#1a1a1a]">
          <CardHeader>
            <CardTitle className="text-[#ededed]">Subscription Summary</CardTitle>
            <CardDescription className="text-[#737373]">
              Trade activity per copied trader
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-16 w-full bg-[#262626] rounded-lg" />
                ))}
              </div>
            ) : activeSubscriptions.length === 0 ? (
              <div className="text-center py-12">
                <History className="w-12 h-12 text-[#525252] mx-auto mb-3" />
                <p className="text-[#737373]">No trade history yet</p>
                <p className="text-sm text-[#525252] mt-1">
                  Start copying traders to see your trade history
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {activeSubscriptions.map((sub) => {
                  const pnl = sub.total_pnl || 0;
                  const trades = sub.total_copied_trades || 0;

                  return (
                    <div
                      key={sub.id}
                      className="flex items-center justify-between p-4 rounded-lg bg-[#0A0A0A] border border-[#1a1a1a]"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#3B82F6] to-[#1D4ED8] flex items-center justify-center text-white font-bold">
                          {sub.leader_profile?.alias?.[0] || "T"}
                        </div>
                        <div>
                          <p className="font-medium text-[#ededed]">
                            {sub.leader_profile?.alias || "Unknown Trader"}
                          </p>
                          <div className="flex items-center gap-3 text-xs text-[#737373] mt-1">
                            <span>{trades} trades</span>
                            <Badge
                              variant={sub.status === "ACTIVE" ? "success" : "outline"}
                              className="text-[9px]"
                            >
                              {sub.status}
                            </Badge>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-8">
                        <div className="text-right">
                          <p className="text-xs text-[#737373]">Allocation</p>
                          <p className="font-mono text-[#ededed]">
                            {formatCurrency(sub.allocation_amount, "NGN")}
                          </p>
                        </div>
                        <div className="text-right min-w-[100px]">
                          <p className="text-xs text-[#737373]">Total P&L</p>
                          <p className={cn(
                            "font-mono font-bold",
                            pnl >= 0 ? "text-[#22C55E]" : "text-[#EF4444]"
                          )}>
                            {pnl >= 0 ? "+" : ""}{formatCurrency(pnl, "NGN")}
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Info Note */}
        <Card className="bg-[#3B82F6]/5 border-[#3B82F6]/20">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <Clock className="w-5 h-5 text-[#3B82F6] flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-[#ededed]">
                  Detailed Trade History
                </p>
                <p className="text-sm text-[#737373] mt-1">
                  Individual trade details are available when viewing each subscription.
                  Click on a subscription to see all executed trades with timestamps,
                  prices, and execution latency.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}

