"use client";

import React, { useState } from "react";
import { DashboardLayout } from "@/components/dashboard/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useLedger, useWalletBalance } from "@/hooks/use-queries";
import { cn, formatCurrency } from "@/lib/utils";
import {
  ArrowUpRight,
  ArrowDownRight,
  Download,
  Filter,
  Search,
  ChevronLeft,
  ChevronRight,
  Wallet,
  TrendingUp,
  TrendingDown,
  RefreshCw,
} from "lucide-react";

// Transaction type badge colors
const transactionTypeConfig: Record<string, { label: string; color: string; icon: typeof ArrowUpRight }> = {
  DEPOSIT: { label: "Deposit", color: "bg-[#22C55E]/10 text-[#22C55E]", icon: ArrowDownRight },
  WITHDRAWAL: { label: "Withdrawal", color: "bg-[#EF4444]/10 text-[#EF4444]", icon: ArrowUpRight },
  TRADE_PNL: { label: "Trade P&L", color: "bg-[#3B82F6]/10 text-[#3B82F6]", icon: TrendingUp },
  FEE: { label: "Fee", color: "bg-[#737373]/10 text-[#737373]", icon: ArrowUpRight },
  PROFIT_SHARE: { label: "Profit Share", color: "bg-[#D4A574]/10 text-[#D4A574]", icon: ArrowUpRight },
  REFERRAL: { label: "Referral", color: "bg-[#22C55E]/10 text-[#22C55E]", icon: ArrowDownRight },
  ADJUSTMENT: { label: "Adjustment", color: "bg-[#737373]/10 text-[#737373]", icon: RefreshCw },
};

export default function LedgerPage() {
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState<string | undefined>(undefined);

  const { data: ledgerData, isLoading, refetch } = useLedger({ page, page_size: 20, transaction_type: filter });
  const { data: walletData, isLoading: walletLoading } = useWalletBalance();

  const entries = ledgerData?.items || [];
  const totalPages = ledgerData?.total_pages || 1;
  const totalBalance = walletData?.reduce((sum, acc) => sum + (acc.balance || 0), 0) || 0;

  const handleExport = () => {
    // TODO: Implement CSV export
    console.log("Export ledger");
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-[#ededed]">Ledger</h1>
            <p className="text-sm text-[#737373] mt-1">
              Complete audit trail of all account transactions
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="outline" onClick={() => refetch()} className="border-[#262626] text-[#a1a1a1]">
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
            <Button variant="outline" onClick={handleExport} className="border-[#262626] text-[#a1a1a1]">
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="bg-[#111111] border-[#1a1a1a]">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-[#737373]">Current Balance</p>
                  {walletLoading ? (
                    <Skeleton className="h-8 w-32 bg-[#262626] mt-1" />
                  ) : (
                    <p className="text-2xl font-bold font-mono text-[#ededed]">
                      {formatCurrency(totalBalance, "NGN")}
                    </p>
                  )}
                </div>
                <div className="w-12 h-12 rounded-xl bg-[#3B82F6]/10 flex items-center justify-center">
                  <Wallet className="w-6 h-6 text-[#3B82F6]" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-[#111111] border-[#1a1a1a]">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-[#737373]">Total Entries</p>
                  {isLoading ? (
                    <Skeleton className="h-8 w-20 bg-[#262626] mt-1" />
                  ) : (
                    <p className="text-2xl font-bold font-mono text-[#ededed]">
                      {ledgerData?.total || 0}
                    </p>
                  )}
                </div>
                <div className="w-12 h-12 rounded-xl bg-[#22C55E]/10 flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-[#22C55E]" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-[#111111] border-[#1a1a1a]">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-[#737373]">Filter</p>
                  <select
                    value={filter || ""}
                    onChange={(e) => setFilter(e.target.value || undefined)}
                    className="mt-1 h-8 rounded-md bg-[#0A0A0A] border border-[#262626] text-[#ededed] text-sm px-2"
                  >
                    <option value="">All Types</option>
                    <option value="DEPOSIT">Deposits</option>
                    <option value="WITHDRAWAL">Withdrawals</option>
                    <option value="TRADE_PNL">Trade P&L</option>
                    <option value="FEE">Fees</option>
                    <option value="PROFIT_SHARE">Profit Share</option>
                  </select>
                </div>
                <div className="w-12 h-12 rounded-xl bg-[#737373]/10 flex items-center justify-center">
                  <Filter className="w-6 h-6 text-[#737373]" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Ledger Table */}
        <Card className="bg-[#111111] border-[#1a1a1a]">
          <CardHeader>
            <CardTitle className="text-[#ededed]">Transaction History</CardTitle>
            <CardDescription className="text-[#737373]">
              Showing {entries.length} of {ledgerData?.total || 0} entries
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="flex items-center justify-between p-4 rounded-lg bg-[#0A0A0A]">
                    <div className="flex items-center gap-4">
                      <Skeleton className="w-10 h-10 rounded-lg bg-[#262626]" />
                      <div>
                        <Skeleton className="h-4 w-24 bg-[#262626] mb-2" />
                        <Skeleton className="h-3 w-32 bg-[#262626]" />
                      </div>
                    </div>
                    <Skeleton className="h-6 w-20 bg-[#262626]" />
                  </div>
                ))}
              </div>
            ) : entries.length === 0 ? (
              <div className="text-center py-12">
                <Wallet className="w-12 h-12 text-[#525252] mx-auto mb-3" />
                <p className="text-[#737373]">No transactions found</p>
              </div>
            ) : (
              <div className="space-y-2">
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
                        <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center", config.color.split(" ")[0])}>
                          <Icon className={cn("w-5 h-5", config.color.split(" ")[1])} />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-[#ededed]">{config.label}</p>
                            <Badge variant="outline" className="text-[9px] border-[#262626] text-[#737373]">
                              {entry.currency}
                            </Badge>
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
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-6 pt-4 border-t border-[#1a1a1a]">
                <p className="text-sm text-[#737373]">
                  Page {page} of {totalPages}
                </p>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="border-[#262626]"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </Button>
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
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}

