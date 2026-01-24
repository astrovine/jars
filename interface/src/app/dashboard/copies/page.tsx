"use client";

import React, { useState } from "react";
import Link from "next/link";
import { DashboardLayout } from "@/components/dashboard/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  useSubscriptions,
  useStopSubscription,
  usePauseSubscription,
  useResumeSubscription,
  usePauseAllSubscriptions,
} from "@/hooks/use-queries";
import { cn, formatCurrency, formatPercentage } from "@/lib/utils";
import type { Subscription } from "@/types";
import {
  Users,
  MoreVertical,
  Pause,
  Play,
  StopCircle,
  TrendingUp,
  TrendingDown,
  AlertOctagon,
  Settings,
  Plus,
  RefreshCw,
} from "lucide-react";

export default function CopiesPage() {
  const [selectedSubscription, setSelectedSubscription] = useState<Subscription | null>(null);
  const [showStopDialog, setShowStopDialog] = useState(false);
  const [showPauseAllDialog, setShowPauseAllDialog] = useState(false);

  const { data: subscriptions, isLoading, refetch } = useSubscriptions();
  const { mutate: stopSubscription, isPending: isStopping } = useStopSubscription();
  const { mutate: pauseSubscription, isPending: isPausing } = usePauseSubscription();
  const { mutate: resumeSubscription, isPending: isResuming } = useResumeSubscription();
  const { mutate: pauseAll, isPending: isPausingAll } = usePauseAllSubscriptions();

  const activeSubscriptions = subscriptions?.filter(s => s.status === "ACTIVE") || [];
  const pausedSubscriptions = subscriptions?.filter(s => s.status === "PAUSED") || [];
  const stoppedSubscriptions = subscriptions?.filter(s => s.status === "STOPPED") || [];

  const totalPnL = subscriptions?.reduce((sum, s) => sum + (s.total_pnl || 0), 0) || 0;
  const totalAllocated = activeSubscriptions.reduce((sum, s) => sum + (s.allocation_amount || 0), 0);

  const handleStop = (subscription: Subscription) => {
    setSelectedSubscription(subscription);
    setShowStopDialog(true);
  };

  const confirmStop = () => {
    if (selectedSubscription) {
      stopSubscription(selectedSubscription.id, {
        onSuccess: () => {
          setShowStopDialog(false);
          setSelectedSubscription(null);
        },
      });
    }
  };

  const handlePause = (id: string) => {
    pauseSubscription(id);
  };

  const handleResume = (id: string) => {
    resumeSubscription(id);
  };

  const handlePauseAll = () => {
    pauseAll(undefined, {
      onSuccess: () => {
        setShowPauseAllDialog(false);
      },
    });
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-[#ededed]">Active Copies</h1>
            <p className="text-sm text-[#737373] mt-1">
              Manage your copy trading subscriptions
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
            {activeSubscriptions.length > 0 && (
              <Button
                variant="outline"
                onClick={() => setShowPauseAllDialog(true)}
                className="border-[#EF4444]/50 text-[#EF4444] hover:bg-[#EF4444]/10"
              >
                <AlertOctagon className="w-4 h-4 mr-2" />
                Pause All
              </Button>
            )}
            <Link href="/dashboard/traders">
              <Button className="bg-[#3B82F6] hover:bg-[#2563EB]">
                <Plus className="w-4 h-4 mr-2" />
                Copy Trader
              </Button>
            </Link>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-[#111111] border-[#1a1a1a]">
            <CardContent className="p-4">
              <p className="text-sm text-[#737373]">Active Copies</p>
              {isLoading ? (
                <Skeleton className="h-8 w-12 bg-[#262626] mt-1" />
              ) : (
                <p className="text-2xl font-bold font-mono text-[#ededed]">
                  {activeSubscriptions.length}
                </p>
              )}
            </CardContent>
          </Card>

          <Card className="bg-[#111111] border-[#1a1a1a]">
            <CardContent className="p-4">
              <p className="text-sm text-[#737373]">Total Allocated</p>
              {isLoading ? (
                <Skeleton className="h-8 w-28 bg-[#262626] mt-1" />
              ) : (
                <p className="text-2xl font-bold font-mono text-[#ededed]">
                  {formatCurrency(totalAllocated, "NGN")}
                </p>
              )}
            </CardContent>
          </Card>

          <Card className="bg-[#111111] border-[#1a1a1a]">
            <CardContent className="p-4">
              <p className="text-sm text-[#737373]">Total P&L</p>
              {isLoading ? (
                <Skeleton className="h-8 w-24 bg-[#262626] mt-1" />
              ) : (
                <p className={cn(
                  "text-2xl font-bold font-mono",
                  totalPnL >= 0 ? "text-[#22C55E]" : "text-[#EF4444]"
                )}>
                  {totalPnL >= 0 ? "+" : ""}{formatCurrency(totalPnL, "NGN")}
                </p>
              )}
            </CardContent>
          </Card>

          <Card className="bg-[#111111] border-[#1a1a1a]">
            <CardContent className="p-4">
              <p className="text-sm text-[#737373]">Paused</p>
              {isLoading ? (
                <Skeleton className="h-8 w-12 bg-[#262626] mt-1" />
              ) : (
                <p className="text-2xl font-bold font-mono text-[#D4A574]">
                  {pausedSubscriptions.length}
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Active Subscriptions */}
        <Card className="bg-[#111111] border-[#1a1a1a]">
          <CardHeader>
            <CardTitle className="text-[#ededed]">Active Subscriptions</CardTitle>
            <CardDescription className="text-[#737373]">
              Traders currently being copied
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-20 w-full bg-[#262626] rounded-lg" />
                ))}
              </div>
            ) : activeSubscriptions.length === 0 ? (
              <div className="text-center py-12">
                <Users className="w-12 h-12 text-[#525252] mx-auto mb-3" />
                <p className="text-[#737373]">No active subscriptions</p>
                <p className="text-sm text-[#525252] mt-1">
                  Start copying a trader to see them here
                </p>
                <Link href="/dashboard/traders">
                  <Button className="mt-4 bg-[#3B82F6] hover:bg-[#2563EB]">
                    Browse Traders
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                {activeSubscriptions.map((sub) => (
                  <SubscriptionCard
                    key={sub.id}
                    subscription={sub}
                    onPause={() => handlePause(sub.id)}
                    onStop={() => handleStop(sub)}
                    isPausing={isPausing}
                  />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Paused Subscriptions */}
        {pausedSubscriptions.length > 0 && (
          <Card className="bg-[#111111] border-[#1a1a1a]">
            <CardHeader>
              <CardTitle className="text-[#ededed]">Paused Subscriptions</CardTitle>
              <CardDescription className="text-[#737373]">
                Temporarily stopped - no trades being copied
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {pausedSubscriptions.map((sub) => (
                  <SubscriptionCard
                    key={sub.id}
                    subscription={sub}
                    onResume={() => handleResume(sub.id)}
                    onStop={() => handleStop(sub)}
                    isResuming={isResuming}
                    isPaused
                  />
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Stop Confirmation Dialog */}
        <Dialog open={showStopDialog} onOpenChange={setShowStopDialog}>
          <DialogContent className="bg-[#111111] border-[#1a1a1a]">
            <DialogHeader>
              <DialogTitle className="text-[#ededed]">Stop Copying?</DialogTitle>
              <DialogDescription className="text-[#737373]">
                This will permanently stop copying{" "}
                <span className="text-[#ededed] font-medium">
                  {selectedSubscription?.leader_profile?.alias || "this trader"}
                </span>
                . Your existing positions will remain open.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setShowStopDialog(false)}
                className="border-[#262626]"
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={confirmStop}
                disabled={isStopping}
              >
                {isStopping ? "Stopping..." : "Stop Copying"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Pause All Dialog */}
        <Dialog open={showPauseAllDialog} onOpenChange={setShowPauseAllDialog}>
          <DialogContent className="bg-[#111111] border-[#1a1a1a]">
            <DialogHeader>
              <DialogTitle className="text-[#EF4444] flex items-center gap-2">
                <AlertOctagon className="w-5 h-5" />
                Pause All Trading?
              </DialogTitle>
              <DialogDescription className="text-[#737373]">
                This will pause all {activeSubscriptions.length} active subscriptions.
                No new trades will be executed until you resume.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setShowPauseAllDialog(false)}
                className="border-[#262626]"
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={handlePauseAll}
                disabled={isPausingAll}
              >
                {isPausingAll ? "Pausing..." : "Pause All"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}

// Subscription Card Component
function SubscriptionCard({
  subscription,
  onPause,
  onResume,
  onStop,
  isPausing,
  isResuming,
  isPaused,
}: {
  subscription: Subscription;
  onPause?: () => void;
  onResume?: () => void;
  onStop: () => void;
  isPausing?: boolean;
  isResuming?: boolean;
  isPaused?: boolean;
}) {
  const pnl = subscription.total_pnl || 0;
  const isProfit = pnl >= 0;
  const allocation = subscription.allocation_amount || 0;
  const pnlPercentage = allocation > 0 ? (pnl / allocation) * 100 : 0;

  return (
    <div className={cn(
      "flex items-center justify-between p-4 rounded-lg bg-[#0A0A0A] border border-[#1a1a1a] transition-colors",
      isPaused && "opacity-70"
    )}>
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-[#3B82F6] to-[#1D4ED8] flex items-center justify-center text-white font-bold text-lg">
          {subscription.leader_profile?.alias?.[0] || "T"}
        </div>
        <div>
          <div className="flex items-center gap-2">
            <p className="font-medium text-[#ededed]">
              {subscription.leader_profile?.alias || "Unknown Trader"}
            </p>
            <Badge
              variant={isPaused ? "warning" : "success"}
              className="text-[9px]"
            >
              {subscription.status}
            </Badge>
          </div>
          <p className="text-xs text-[#737373] mt-1">
            {subscription.total_copied_trades || 0} trades copied
          </p>
        </div>
      </div>

      <div className="flex items-center gap-8">
        <div className="text-right">
          <p className="text-xs text-[#737373]">Allocation</p>
          <p className="font-mono text-[#ededed]">
            {formatCurrency(allocation, "NGN")}
          </p>
        </div>

        <div className="text-right min-w-[100px]">
          <p className="text-xs text-[#737373]">P&L</p>
          <div className="flex items-center justify-end gap-1">
            {isProfit ? (
              <TrendingUp className="w-4 h-4 text-[#22C55E]" />
            ) : (
              <TrendingDown className="w-4 h-4 text-[#EF4444]" />
            )}
            <span className={cn(
              "font-mono font-bold",
              isProfit ? "text-[#22C55E]" : "text-[#EF4444]"
            )}>
              {formatPercentage(pnlPercentage)}
            </span>
          </div>
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="text-[#737373] hover:text-[#ededed]">
              <MoreVertical className="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="bg-[#111111] border-[#1a1a1a]">
            {isPaused ? (
              <DropdownMenuItem
                onClick={onResume}
                disabled={isResuming}
                className="text-[#22C55E] focus:bg-[#22C55E]/10"
              >
                <Play className="w-4 h-4 mr-2" />
                {isResuming ? "Resuming..." : "Resume"}
              </DropdownMenuItem>
            ) : (
              <DropdownMenuItem
                onClick={onPause}
                disabled={isPausing}
                className="text-[#D4A574] focus:bg-[#D4A574]/10"
              >
                <Pause className="w-4 h-4 mr-2" />
                {isPausing ? "Pausing..." : "Pause"}
              </DropdownMenuItem>
            )}
            <DropdownMenuSeparator className="bg-[#1a1a1a]" />
            <DropdownMenuItem
              onClick={onStop}
              className="text-[#EF4444] focus:bg-[#EF4444]/10"
            >
              <StopCircle className="w-4 h-4 mr-2" />
              Stop Copying
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}

