"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "@/components/ui/resizable";
import {
    LayoutDashboard,
    Users,
    Wallet,
    Key,
    History,
    Settings,
    Shield,
    BookOpen,
    PieChart,
    Search,
    Bell,
    LogOut,
    Terminal
} from "lucide-react";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { useAuth } from "@/components/auth/auth-provider";

const navigation = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Traders", href: "/dashboard/traders", icon: Users },
    { name: "My Copies", href: "/dashboard/copies", icon: PieChart },
    { name: "Portfolio", href: "/dashboard/portfolio", icon: PieChart },
    { name: "Wallet", href: "/dashboard/wallet", icon: Wallet },
    { name: "Ledger", href: "/dashboard/ledger", icon: BookOpen },
    { name: "History", href: "/dashboard/history", icon: History },
    { name: "API Keys", href: "/dashboard/keys", icon: Key },
    { name: "Security", href: "/dashboard/security", icon: Shield },
    { name: "Settings", href: "/dashboard/settings", icon: Settings },
];

export function BloombergLayout({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const { user, logout } = useAuth();

    return (
        <TooltipProvider>
            <div className="h-screen w-full bg-[#000000] text-[#a1a1aa] flex flex-col font-mono text-xs overflow-hidden selection:bg-emerald-500/30">
                {/* Header / Command Bar */}
                <header className="h-10 border-b border-white/10 flex items-center px-4 gap-4 bg-[#050505]">
                    <div className="flex items-center gap-2">
                        <Terminal className="w-4 h-4 text-emerald-500" />
                        <span className="font-bold text-emerald-500 tracking-widest hidden sm:inline-block">JARS<span className="text-white/40 font-normal">OS</span></span>
                    </div>

                    <div className="h-4 w-[1px] bg-white/10 mx-2" />

                    {/* Command Input */}
                    <div className="flex-1 max-w-xl relative group">
                        <Search className="absolute left-2 top-1.5 w-3.5 h-3.5 text-neutral-500 group-focus-within:text-emerald-500 transition-colors" />
                        <Input
                            className="h-7 pl-8 bg-white/5 border-transparent hover:border-white/10 focus:border-emerald-500/50 text-[11px] font-mono rounded-sm focus-visible:ring-0 text-emerald-100 placeholder:text-neutral-600 transition-all uppercase"
                            placeholder="ENTER COMMAND OR SEARCH FUNCTION..."
                        />
                    </div>

                    <div className="ml-auto flex items-center gap-6 text-[10px] text-neutral-500 uppercase tracking-wider font-medium">
                        <div className="hidden md:flex items-center gap-2">
                            <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                            <span>NET: ONLINE</span>
                        </div>
                        <div className="hidden md:flex items-center gap-4">
                            <span>LAT: <span className="text-emerald-500">12ms</span></span>
                            <span>CPU: <span className="text-emerald-500">4%</span></span>
                            <span>MEM: <span className="text-emerald-500">128MB</span></span>
                        </div>

                        <div className="h-4 w-[1px] bg-white/10" />

                        <div className="flex items-center gap-3">
                            <span className="text-emerald-500">{user?.email}</span>
                            <button onClick={logout} className="hover:text-white transition-colors">
                                <LogOut className="w-3.5 h-3.5" />
                            </button>
                        </div>
                    </div>
                </header>

                <ResizablePanelGroup direction="horizontal" className="flex-1">
                    {/* Sidebar */}
                    <ResizablePanel defaultSize={4} minSize={4} maxSize={15} className="bg-[#050505] border-r border-white/10 flex flex-col items-center py-4 gap-1">
                        {navigation.map((item) => {
                            const isActive = pathname === item.href;
                            return (
                                <Tooltip key={item.name} delayDuration={0}>
                                    <TooltipTrigger asChild>
                                        <Link
                                            href={item.href}
                                            className={cn(
                                                "p-2.5 rounded-sm transition-all duration-200 group relative w-10 h-10 flex items-center justify-center",
                                                isActive
                                                    ? "bg-emerald-500/10 text-emerald-500 shadow-[inset_2px_0_0_0_#10b981]"
                                                    : "text-neutral-500 hover:text-white hover:bg-white/5"
                                            )}
                                        >
                                            <item.icon className="w-4 h-4" />
                                            {isActive && <div className="absolute inset-0 bg-emerald-500/5 animate-pulse-subtle pointer-events-none" />}
                                        </Link>
                                    </TooltipTrigger>
                                    <TooltipContent
                                        side="right"
                                        className="bg-[#0a0a0a] border border-white/10 text-[10px] uppercase font-mono tracking-wider text-emerald-500 shadow-xl"
                                    >
                                        <p>{item.name}</p>
                                    </TooltipContent>
                                </Tooltip>
                            );
                        })}
                    </ResizablePanel>

                    <ResizableHandle className="bg-white/5 hover:bg-emerald-500/50 transition-colors w-[1px]" />

                    {/* Main Content */}
                    <ResizablePanel defaultSize={75} className="bg-[#000]">
                        <div className="h-full overflow-y-auto w-full">
                            {children}
                        </div>
                    </ResizablePanel>

                    <ResizableHandle className="bg-white/5 hover:bg-emerald-500/50 transition-colors w-[1px]" />

                    {/* Right Panel: Watchlist / Ticker */}
                    <ResizablePanel defaultSize={21} minSize={15} maxSize={30} className="bg-[#050505] border-l border-white/10 hidden xl:flex flex-col">
                        <div className="h-8 border-b border-white/10 flex items-center px-3 bg-[#0a0a0a]">
                            <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest flex items-center gap-2">
                                <Activity className="w-3 h-3 text-emerald-500" />
                                Market Watch
                            </span>
                        </div>
                        <div className="flex-1 overflow-y-auto p-0">
                            {/* Mock Market Data */}
                            {[
                                { pair: "BTC/USDT", price: "94,320.50", change: "+2.4%", up: true },
                                { pair: "ETH/USDT", price: "5,102.10", change: "+1.8%", up: true },
                                { pair: "SOL/USDT", price: "189.45", change: "-0.5%", up: false },
                                { pair: "BNB/USDT", price: "612.30", change: "+0.2%", up: true },
                                { pair: "XRP/USDT", price: "1.24", change: "-1.1%", up: false },
                            ].map((coin, i) => (
                                <div key={i} className="flex items-center justify-between py-2 px-3 border-b border-white/5 hover:bg-white/5 cursor-pointer transition-colors group">
                                    <div className="flex flex-col">
                                        <span className="font-bold text-white group-hover:text-emerald-400 transition-colors">{coin.pair}</span>
                                        <span className="text-[9px] text-neutral-600">BINANCE</span>
                                    </div>
                                    <div className="flex flex-col items-end">
                                        <span className="text-white tab-nums">{coin.price}</span>
                                        <span className={cn("text-[9px] tab-nums", coin.up ? "text-emerald-500" : "text-red-500")}>
                                            {coin.change}
                                        </span>
                                    </div>
                                </div>
                            ))}

                            <div className="mt-6 h-8 border-b border-t border-white/10 flex items-center px-3 bg-[#0a0a0a]">
                                <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest flex items-center gap-2">
                                    <Bell className="w-3 h-3 text-amber-500" />
                                    Alerts
                                </span>
                            </div>
                            <div className="p-3 text-[10px] text-neutral-500 space-y-3">
                                <div className="flex gap-2">
                                    <span className="text-amber-500 font-bold">12:04:11</span>
                                    <span>Large withdrawal BTC detected (Whale Alert)</span>
                                </div>
                                <div className="flex gap-2">
                                    <span className="text-emerald-500 font-bold">11:58:22</span>
                                    <span>Strategy "Alpha" executed BUY ETH</span>
                                </div>
                            </div>
                        </div>
                    </ResizablePanel>
                </ResizablePanelGroup>

                {/* Footer */}
                <footer className="h-6 border-t border-white/10 bg-[#050505] flex items-center justify-between px-3 text-[9px] text-neutral-600 uppercase tracking-widest font-mono">
                    <div className="flex items-center gap-4">
                        <span>JARS TERMINAL &copy; 2026</span>
                        <span className="text-neutral-700">|</span>
                        <span>BUILD: 2.0.4-RC</span>
                        <span className="text-neutral-700">|</span>
                        <span className="text-emerald-800">ENCRYPTION: AES-256-GCM</span>
                    </div>
                    <div className="flex items-center gap-4">
                        <span className="flex items-center gap-1"><span className="w-1 h-1 bg-emerald-500 rounded-full" /> WS: CONNECTED</span>
                        <span>AUDIT: ACTIVE</span>
                    </div>
                </footer>
            </div>
        </TooltipProvider>
    );
}

function Activity({ className }: { className?: string }) {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={className}
        >
            <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
        </svg>
    )
}
