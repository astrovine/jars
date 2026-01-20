"use client";

import React from "react";
import { DashboardLayout } from "@/components/dashboard/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useSubscriptions, useWalletBalance } from "@/hooks/use-queries";
import { cn, formatCurrency, formatPercentage } from "@/lib/utils";
import Link from "next/link";
import {
  TrendingUp,
  TrendingDown,
  Wallet,
  Users,
  PieChart,
  ArrowUpRight,
  ArrowDownRight,
  Activity,
} from "lucide-react";

// Simple Pie Chart Component
function AllocationChart({ data }: { data: { name: string; value: number; color: string }[] }) {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  if (total === 0) return null;

  let currentAngle = 0;
  const paths = data.map((item, index) => {
    const percentage = item.value / total;
    const angle = percentage * 360;
    const startAngle = currentAngle;
    const endAngle = currentAngle + angle;
    currentAngle = endAngle;

    const startRad = (startAngle - 90) * (Math.PI / 180);
    const endRad = (endAngle - 90) * (Math.PI / 180);

    const x1 = 50 + 40 * Math.cos(startRad);
    const y1 = 50 + 40 * Math.sin(startRad);
    const x2 = 50 + 40 * Math.cos(endRad);
    const y2 = 50 + 40 * Math.sin(endRad);

    const largeArc = angle > 180 ? 1 : 0;

    return (
      <path
        key={index}
        d={`M 50 50 L ${x1} ${y1} A 40 40 0 ${largeArc} 1 ${x2} ${y2} Z`}
        fill={item.color}
        stroke="#0A0A0A"
        strokeWidth="1"
      />
    );
  });

  return (
    <svg viewBox="0 0 100 100" className="w-full h-full">
      {paths}
      <circle cx="50" cy="50" r="25" fill="#0A0A0A" />
    </svg>
  );
}

export default function PortfolioPage() {
  const { data: subscriptions, isLoading: subsLoading } = useSubscriptions();
  const { data: walletData, isLoading: walletLoading } = useWalletBalance();

  const isLoading = subsLoading || walletLoading;

  const activeSubscriptions = subscriptions?.filter(s => s.status === "ACTIVE") || [];
  const totalBalance = walletData?.reduce((sum, acc) => sum + (acc.balance || 0), 0) || 0;
  const totalAllocated = activeSubscriptions.reduce((sum, s) => sum + (s.allocation_amount || 0), 0);
  const totalPnL = activeSubscriptions.reduce((sum, s) => sum + (s.total_pnl || 0), 0);
  const availableBalance = totalBalance - totalAllocated;

  // Allocation data for chart
  const allocationData = activeSubscriptions.map((sub, idx) => ({
    name: sub.leader_profile?.alias || `Trader ${idx + 1}`,
    value: sub.allocation_amount,
    color: `hsl(${(idx * 60) % 360}, 70%, 50%)`,
  }));

  if (availableBalance > 0) {
    allocationData.push({
      name: "Available",
      value: availableBalance,
      color: "#525252",
    });
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-[#ededed]">Portfolio</h1>
            <p className="text-sm text-[#737373] mt-1">
              Overview of your trading portfolio and allocations
            </p>
          </div>
          <Link href="/dashboard/traders">
            <Button className="bg-[#3B82F6] hover:bg-[#2563EB]">
              <Users className="w-4 h-4 mr-2" />
              Copy New Trader
            </Button>
          </Link>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-[#111111] border-[#1a1a1a]">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-[#737373]">Total Balance</p>
                  {isLoading ? (
                    <Skeleton className="h-8 w-28 bg-[#262626] mt-1" />
                  ) : (
                    <p className="text-2xl font-bold font-mono text-[#ededed]">
                      {formatCurrency(totalBalance, "NGN")}
                    </p>
                  )}
                </div>
                <div className="w-10 h-10 rounded-lg bg-[#3B82F6]/10 flex items-center justify-center">
                  <Wallet className="w-5 h-5 text-[#3B82F6]" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-[#111111] border-[#1a1a1a]">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-[#737373]">Allocated</p>
                  {isLoading ? (
                    <Skeleton className="h-8 w-28 bg-[#262626] mt-1" />
                  ) : (
                    <p className="text-2xl font-bold font-mono text-[#ededed]">
                      {formatCurrency(totalAllocated, "NGN")}
                    </p>
                  )}
                </div>
                <div className="w-10 h-10 rounded-lg bg-[#D4A574]/10 flex items-center justify-center">
                  <PieChart className="w-5 h-5 text-[#D4A574]" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-[#111111] border-[#1a1a1a]">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-[#737373]">Available</p>
                  {isLoading ? (
                    <Skeleton className="h-8 w-28 bg-[#262626] mt-1" />
                  ) : (
                    <p className="text-2xl font-bold font-mono text-[#ededed]">
                      {formatCurrency(availableBalance, "NGN")}
                    </p>
                  )}
                </div>
                <div className="w-10 h-10 rounded-lg bg-[#22C55E]/10 flex items-center justify-center">
                  <Activity className="w-5 h-5 text-[#22C55E]" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-[#111111] border-[#1a1a1a]">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-[#737373]">Total P&L</p>
                  {isLoading ? (
                    <Skeleton className="h-8 w-28 bg-[#262626] mt-1" />
                  ) : (
                    <p className={cn(
                      "text-2xl font-bold font-mono",
                      totalPnL >= 0 ? "text-[#22C55E]" : "text-[#EF4444]"
                    )}>
                      {totalPnL >= 0 ? "+" : ""}{formatCurrency(totalPnL, "NGN")}
                    </p>
                  )}
                </div>
                <div className={cn(
                  "w-10 h-10 rounded-lg flex items-center justify-center",
                  totalPnL >= 0 ? "bg-[#22C55E]/10" : "bg-[#EF4444]/10"
                )}>
                  {totalPnL >= 0 ? (
                    <TrendingUp className="w-5 h-5 text-[#22C55E]" />
                  ) : (
                    <TrendingDown className="w-5 h-5 text-[#EF4444]" />
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Allocation Chart & List */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chart */}
          <Card className="bg-[#111111] border-[#1a1a1a]">
            <CardHeader>
              <CardTitle className="text-[#ededed]">Allocation</CardTitle>
              <CardDescription className="text-[#737373]">
                How your capital is distributed
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="w-48 h-48 mx-auto">
                {isLoading ? (
                  <Skeleton className="w-full h-full rounded-full bg-[#262626]" />
                ) : allocationData.length > 0 ? (
                  <AllocationChart data={allocationData} />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <p className="text-[#737373] text-sm">No allocations</p>
                  </div>
                )}
              </div>

              {/* Legend */}
              <div className="mt-4 space-y-2">
                {allocationData.map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-sm"
                        style={{ backgroundColor: item.color }}
                      />
                      <span className="text-[#a1a1a1]">{item.name}</span>
                    </div>
                    <span className="font-mono text-[#ededed]">
                      {formatCurrency(item.value, "NGN")}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Active Subscriptions */}
          <Card className="lg:col-span-2 bg-[#111111] border-[#1a1a1a]">
            <CardHeader>
              <CardTitle className="text-[#ededed]">Active Copies</CardTitle>
              <CardDescription className="text-[#737373]">
                Traders you are currently copying
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
                <div className="text-center py-8">
                  <Users className="w-12 h-12 text-[#525252] mx-auto mb-3" />
                  <p className="text-[#737373] mb-4">No active copies</p>
                  <Link href="/dashboard/traders">
                    <Button className="bg-[#3B82F6] hover:bg-[#2563EB]">
                      Browse Traders
                    </Button>
                  </Link>
                </div>
              ) : (
                <div className="space-y-3">
                  {activeSubscriptions.map((sub) => {
                    const pnl = sub.total_pnl || 0;
                    const pnlPercentage = sub.allocation_amount > 0
                      ? (pnl / sub.allocation_amount) * 100
                      : 0;

                    return (
                      <div
                        key={sub.id}
                        className="flex items-center justify-between p-4 rounded-lg bg-[#0A0A0A] border border-[#1a1a1a] hover:border-[#262626] transition-colors"
                      >
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#3B82F6] to-[#1D4ED8] flex items-center justify-center text-white font-bold">
                            {sub.leader_profile?.alias?.[0] || "T"}
                          </div>
                          <div>
                            <p className="font-medium text-[#ededed]">
                              {sub.leader_profile?.alias || "Unknown Trader"}
                            </p>
                            <p className="text-xs text-[#737373]">
                              {sub.total_copied_trades || 0} trades
                            </p>
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
                            <p className="text-xs text-[#737373]">P&L</p>
                            <div className="flex items-center justify-end gap-1">
                              {pnl >= 0 ? (
                                <ArrowUpRight className="w-4 h-4 text-[#22C55E]" />
                              ) : (
                                <ArrowDownRight className="w-4 h-4 text-[#EF4444]" />
                              )}
                              <span className={cn(
                                "font-mono font-medium",
                                pnl >= 0 ? "text-[#22C55E]" : "text-[#EF4444]"
                              )}>
                                {formatPercentage(pnlPercentage)}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}

