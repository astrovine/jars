"use client";

import React from "react";
import Link from "next/link";
import { useWalletBalance, useSubscriptions } from "@/hooks/use-queries";
import { ProfitChart } from "@/components/dashboard/profit-chart";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ArrowUpRight, MoreHorizontal, Play, Pause, AlertTriangle } from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import { cn } from "@/lib/utils";

// Mock Ledger Data
const ledgerEntries = [
  { time: "12:04:45", type: "EXECUTION", message: "Buy 0.5 ETH @ $3,450.00 (Strategy Alpha)", status: "success" },
  { time: "12:03:12", type: "SYNC", message: "Portfolio rebalanced", status: "info" },
  { time: "11:55:00", type: "SYSTEM", message: "Risk check passed (Delta < 0.2)", status: "success" },
  { time: "11:42:15", type: "EXECUTION", message: "Sell 100 SOL @ $142.50 (Strategy Beta)", status: "success" },
  { time: "11:30:00", type: "DEPOSIT", message: "Incoming deposit detected: 0.2 BTC", status: "info" },
  { time: "11:15:22", type: "WARNING", message: "High latency detected on Exchange A (150ms)", status: "warning" },
  { time: "10:59:59", type: "EXECUTION", message: "Buy 1000 XRP @ $0.62 (Strategy Gamma)", status: "success" },
];

export default function DashboardPage() {
  const { data: accounts, isLoading: loadingBalance } = useWalletBalance();
  const { data: subscriptions, isLoading: loadingSubs } = useSubscriptions();

  const totalBalance = accounts?.reduce((sum, acc) => sum + (acc.balance || 0), 0) || 0;
  const activeSubs = subscriptions?.filter((s) => s.status === "ACTIVE") || [];

  // Mock PnL
  const totalPnl = 1250.45;
  const pnlPercent = 4.2;

  return (
    <div className="p-2 space-y-2 min-h-full">
      {/* Top Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2">
        <MetricCard
          label="NET LIQUIDATION"
          value={formatCurrency(totalBalance)}
          change="+0.0%"
          sub="Total Equity"
        />
        <MetricCard
          label="UNREALIZED P&L"
          value={formatCurrency(totalPnl)}
          change={`+${pnlPercent}%`}
          color="text-emerald-500"
          sub="Open Positions"
        />
        <MetricCard
          label="ACTIVE JARS"
          value={activeSubs.length.toString()}
          sub={`${subscriptions?.length || 0} Total Configured`}
          color="text-neutral-200"
        />
        <MetricCard
          label="MARGIN LEVEL"
          value="999%"
          change="Safe"
          color="text-emerald-500"
          sub="Risk Status"
        />
      </div>

      {/* Main Split: Chart & Ledger */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-2 h-[350px]">
        {/* Chart Section */}
        <div className="lg:col-span-2 flex flex-col">
          <ProfitChart />
        </div>

        {/* Live Ledger Section */}
        <div className="bg-[#050505] border border-white/10 flex flex-col overflow-hidden">
          <div className="px-3 py-2 border-b border-white/10 bg-[#0a0a0a] flex items-center justify-between">
            <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest flex items-center gap-2">
              <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
              Live Feed
            </span>
            <Badge variant="outline" className="text-[9px] h-4 border-white/10 text-neutral-500">
              SYSTEM
            </Badge>
          </div>
          <ScrollArea className="flex-1 bg-[#020202]">
            <div className="flex flex-col">
              {ledgerEntries.map((entry, i) => (
                <div key={i} className="flex gap-3 px-3 py-2 border-b border-white/5 font-mono text-[10px] hover:bg-white/5 transition-colors cursor-pointer">
                  <span className="text-neutral-500 min-w-[50px]">{entry.time}</span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className={cn(
                        "font-bold uppercase",
                        entry.status === 'success' ? 'text-emerald-500' :
                          entry.status === 'warning' ? 'text-amber-500' : 'text-blue-500'
                      )}>{entry.type}</span>
                    </div>
                    <span className="text-neutral-300">{entry.message}</span>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>
      </div>

      {/* Bottom: Active Allocations */}
      <div className="bg-[#050505] border border-white/10 flex flex-col">
        <div className="px-3 py-2 border-b border-white/10 bg-[#0a0a0a] flex items-center justify-between">
          <h3 className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest">Active Jar Allocations</h3>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" className="h-6 text-[10px] border-white/10 bg-transparent text-neutral-400 hover:text-white uppercase">
              Risk Assessment
            </Button>
            <Link href="/dashboard/traders">
              <Button size="sm" className="h-6 text-[10px] bg-emerald-900/30 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/20 uppercase">
                + Deploy New Jar
              </Button>
            </Link>
          </div>
        </div>

        <Table>
          <TableHeader className="bg-[#0a0a0a] border-b border-white/10">
            <TableRow className="hover:bg-transparent border-transparent">
              <TableHead className="h-8 text-[9px] uppercase font-bold text-neutral-500 tracking-wider">Strategy / Trader</TableHead>
              <TableHead className="h-8 text-[9px] uppercase font-bold text-neutral-500 tracking-wider text-right">Allocated</TableHead>
              <TableHead className="h-8 text-[9px] uppercase font-bold text-neutral-500 tracking-wider text-right">PnL (Open)</TableHead>
              <TableHead className="h-8 text-[9px] uppercase font-bold text-neutral-500 tracking-wider text-right">ROI</TableHead>
              <TableHead className="h-8 text-[9px] uppercase font-bold text-neutral-500 tracking-wider text-center">Status</TableHead>
              <TableHead className="h-8 text-[9px] uppercase font-bold text-neutral-500 tracking-wider text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody className="bg-[#000]">
            {activeSubs.length > 0 ? activeSubs.map((sub) => (
              <TableRow key={sub.id} className="border-b border-white/5 hover:bg-white/5 group text-[11px] font-mono">
                <TableCell className="font-medium text-white group-hover:text-emerald-400 transition-colors">
                  {sub.trader_id}
                </TableCell>
                <TableCell className="text-right text-neutral-300">
                  {formatCurrency(sub.allocation_amount)}
                </TableCell>
                <TableCell className="text-right text-emerald-500">
                  +$142.50
                </TableCell>
                <TableCell className="text-right text-emerald-500">
                  +12.4%
                </TableCell>
                <TableCell className="text-center">
                  <Badge variant="outline" className="border-emerald-500/30 text-emerald-500 bg-emerald-500/10 text-[9px] uppercase rounded-sm px-1.5 py-0 h-4 min-w-[60px] justify-center">
                    Running
                  </Badge>
                </TableCell>
                <TableCell className="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" className="h-6 w-6 text-neutral-500 hover:text-white">
                        <MoreHorizontal className="w-3 h-3" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="bg-[#0a0a0a] border-white/10 text-white">
                      <DropdownMenuItem className="text-[10px] uppercase font-mono hover:bg-white/10 cursor-pointer">View Details</DropdownMenuItem>
                      <DropdownMenuItem className="text-[10px] uppercase font-mono hover:bg-white/10 cursor-pointer text-amber-500">Pause Copy</DropdownMenuItem>
                      <DropdownMenuItem className="text-[10px] uppercase font-mono hover:bg-white/10 cursor-pointer text-red-500">Stop & Close</DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            )) : (
              <TableRow className="border-transparent">
                <TableCell colSpan={6} className="h-32 text-center">
                  <div className="flex flex-col items-center justify-center text-neutral-600 gap-2">
                    <AlertTriangle className="w-6 h-6 opacity-50" />
                    <p className="text-xs uppercase tracking-widest">No Active Allocations</p>
                    <Link href="/dashboard/traders">
                      <Button size="sm" variant="link" className="text-emerald-500 h-auto p-0 text-xs">
                        Initialize Strategy &rarr;
                      </Button>
                    </Link>
                  </div>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

function MetricCard({ label, value, change, sub, color = "text-white" }: { label: string, value: string, change?: string, sub?: string, color?: string }) {
  return (
    <div className="bg-[#050505] border border-white/10 p-3 hover:border-emerald-500/30 transition-colors group">
      <h3 className="text-[10px] uppercase font-bold text-neutral-500 tracking-wider mb-1">{label}</h3>
      <div className="flex items-baseline gap-2">
        <span className={cn("text-2xl font-mono font-medium tracking-tighter", color)}>{value}</span>
        {change && (
          <Badge variant="outline" className={cn("text-[9px] h-4 rounded-sm px-1 border-transparent bg-white/5", change.startsWith('+') ? 'text-emerald-500' : 'text-red-500')}>
            {change}
          </Badge>
        )}
      </div>
      {sub && <p className="text-[9px] text-neutral-600 mt-1 uppercase group-hover:text-neutral-400 transition-colors">{sub}</p>}
    </div>
  )
}
