"use client";

import React, { useState } from "react";
import { DashboardLayout } from "@/components/dashboard/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useWalletBalance, useLedger } from "@/hooks/use-queries";
import { cn, formatCurrency } from "@/lib/utils";
import {
  Wallet,
  ArrowUpRight,
  ArrowDownRight,
  Plus,
  Minus,
  Clock,
  CheckCircle,
  Shield,
} from "lucide-react";

export default function WalletPage() {
  const [depositOpen, setDepositOpen] = useState(false);
  const [withdrawOpen, setWithdrawOpen] = useState(false);

  const { data: balanceData, isLoading: balanceLoading } = useWalletBalance();
  const { data: ledgerData, isLoading: txLoading } = useLedger({ page_size: 10 });

  // Calculate totals from account array
  const totalBalance = balanceData?.reduce((sum, acc) => sum + (acc.balance || 0), 0) || 0;
  const recentTransactions = ledgerData?.items || [];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-[#ededed]">Wallet</h1>
            <p className="text-sm text-[#737373] mt-1">
              Manage your funds and view transaction history
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="outline" className="border-[#262626]">
              <Minus className="w-4 h-4 mr-2" />
              Withdraw
            </Button>
            <Button className="bg-[#3B82F6] hover:bg-[#2563EB]">
              <Plus className="w-4 h-4 mr-2" />
              Deposit
            </Button>
          </div>
        </div>

        {/* Balance Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="bg-[#111111] border-[#1a1a1a]">
            <CardContent className="pt-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-[#737373] mb-1">Total Balance</p>
                  {balanceLoading ? (
                    <Skeleton className="h-9 w-32 bg-[#262626]" />
                  ) : (
                    <p className="font-mono text-3xl font-bold text-[#ededed]">
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
            <CardContent className="pt-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-[#737373] mb-1">Available</p>
                  {balanceLoading ? (
                    <Skeleton className="h-9 w-32 bg-[#262626]" />
                  ) : (
                    <p className="font-mono text-3xl font-bold text-[#ededed]">
                      {formatCurrency(totalBalance, "NGN")}
                    </p>
                  )}
                </div>
                <div className="w-12 h-12 rounded-xl bg-[#22C55E]/10 flex items-center justify-center">
                  <CheckCircle className="w-6 h-6 text-[#22C55E]" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-[#111111] border-[#1a1a1a]">
            <CardContent className="pt-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-[#737373] mb-1">In Trading</p>
                  {balanceLoading ? (
                    <Skeleton className="h-9 w-32 bg-[#262626]" />
                  ) : (
                    <p className="font-mono text-3xl font-bold text-[#ededed]">
                      {formatCurrency(0, "NGN")}
                    </p>
                  )}
                </div>
                <div className="w-12 h-12 rounded-xl bg-[#D4A574]/10 flex items-center justify-center">
                  <Clock className="w-6 h-6 text-[#D4A574]" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Security Notice */}
        <Card className="bg-[#22C55E]/5 border-[#22C55E]/20">
          <CardContent className="py-4">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg bg-[#22C55E]/20 flex items-center justify-center flex-shrink-0">
                <Shield className="w-5 h-5 text-[#22C55E]" />
              </div>
              <div>
                <h3 className="font-medium text-[#ededed] mb-1">
                  Your funds are protected
                </h3>
                <p className="text-sm text-[#737373]">
                  JARS is a non-custodial platform. Your trading funds remain on your exchange.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Recent Transactions */}
        <Card className="bg-[#111111] border-[#1a1a1a]">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-[#ededed]">
              <Clock className="w-4 h-4" />
              Recent Transactions
            </CardTitle>
          </CardHeader>
          <CardContent>
            {txLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-16 w-full bg-[#262626] rounded-lg" />
                ))}
              </div>
            ) : recentTransactions.length === 0 ? (
              <div className="text-center py-8">
                <Wallet className="w-12 h-12 text-[#525252] mx-auto mb-3" />
                <p className="text-[#737373]">No transactions yet</p>
                <p className="text-sm text-[#525252]">
                  Make your first deposit to get started
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentTransactions.map((tx) => {
                  const isCredit = tx.amount >= 0;
                  return (
                    <div
                      key={tx.id}
                      className="flex items-center gap-4 p-4 rounded-lg bg-[#0A0A0A] border border-[#1a1a1a]"
                    >
                      <div
                        className={cn(
                          "w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0",
                          isCredit ? "bg-[#22C55E]/10" : "bg-[#EF4444]/10"
                        )}
                      >
                        {isCredit ? (
                          <ArrowDownRight className="w-5 h-5 text-[#22C55E]" />
                        ) : (
                          <ArrowUpRight className="w-5 h-5 text-[#EF4444]" />
                        )}
                      </div>

                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-[#ededed]">
                          {tx.transaction_type}
                        </p>
                        <p className="text-xs text-[#737373]">
                          {tx.description || "No description"}
                        </p>
                      </div>

                      <div className="text-right">
                        <p
                          className={cn(
                            "font-mono text-sm font-semibold",
                            isCredit ? "text-[#22C55E]" : "text-[#EF4444]"
                          )}
                        >
                          {isCredit ? "+" : ""}{formatCurrency(tx.amount, tx.currency)}
                        </p>
                        <p className="text-[10px] text-[#525252]">
                          {new Date(tx.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}

