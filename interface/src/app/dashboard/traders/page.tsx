"use client";

import React, { useState } from "react";
import Link from "next/link";
import { DashboardLayout } from "@/components/dashboard/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useTraders } from "@/hooks/use-queries";
import { cn, formatCurrency, formatPercentage } from "@/lib/utils";
import {
  Search,
  Users,
  TrendingUp,
  Award,
  ChevronLeft,
  ChevronRight,
  Star,
  BarChart3,
} from "lucide-react";

export default function TradersPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useTraders({ page, page_size: 12 });

  const traders = data?.items || [];
  const totalPages = data?.total_pages || 1;

  // Filter by search
  const filteredTraders = traders.filter((trader) => {
    if (!search) return true;
    return trader.alias.toLowerCase().includes(search.toLowerCase());
  });

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-[#ededed]">Traders</h1>
            <p className="text-sm text-[#737373] mt-1">
              Browse and copy verified traders
            </p>
          </div>
        </div>

        {/* Search */}
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#525252]" />
          <Input
            placeholder="Search traders..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10 bg-[#0A0A0A] border-[#262626] text-[#ededed]"
          />
        </div>

        {/* Stats */}
        <div className="flex items-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-[#3B82F6]" />
            <span className="font-mono">{data?.total || 0}</span>
            <span className="text-[#737373]">traders</span>
          </div>
          <div className="flex items-center gap-2">
            <Award className="w-4 h-4 text-[#D4A574]" />
            <span className="font-mono">
              {traders.filter((t) => t.status === "ACTIVE").length}
            </span>
            <span className="text-[#737373]">verified</span>
          </div>
        </div>

        {/* Traders Grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Skeleton key={i} className="h-48 bg-[#262626] rounded-xl" />
            ))}
          </div>
        ) : filteredTraders.length === 0 ? (
          <Card className="bg-[#111111] border-[#1a1a1a]">
            <CardContent className="py-12 text-center">
              <Users className="w-12 h-12 text-[#525252] mx-auto mb-4" />
              <h3 className="text-lg font-medium text-[#ededed] mb-2">
                No traders found
              </h3>
              <p className="text-[#737373]">
                {search ? "Try a different search term" : "No traders available yet"}
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredTraders.map((trader) => (
              <Card
                key={trader.id}
                className="bg-[#111111] border-[#1a1a1a] hover:border-[#262626] transition-colors"
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
                          <h3 className="font-semibold text-[#ededed]">
                            {trader.alias}
                          </h3>
                          {trader.status === "ACTIVE" && (
                            <Badge variant="success" className="text-[9px]">
                              Verified
                            </Badge>
                          )}
                          {trader.status === "INCUBATION" && (
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
                        trader.total_pnl >= 0 ? "text-[#22C55E]" : "text-[#EF4444]"
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
                    disabled={trader.status !== "ACTIVE"}
                  >
                    <TrendingUp className="w-4 h-4 mr-2" />
                    Copy Trader
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="border-[#262626]"
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <span className="text-sm text-[#737373]">
              Page {page} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="border-[#262626]"
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

