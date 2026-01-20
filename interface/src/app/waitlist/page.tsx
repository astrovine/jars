"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { SparklesCore } from "@/components/ui/sparkles";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Timeline } from "@/components/ui/timeline";
import { EncryptedText } from "@/components/ui/encrypted-text";
import { supabase } from "@/lib/supabase";
import { Loader2, Terminal, CheckCircle2, Send } from "lucide-react";

export default function WaitlistPage() {
    const [email, setEmail] = useState("");
    const [agreed, setAgreed] = useState(false);
    const [submitted, setSubmitted] = useState(false);
    const [showToast, setShowToast] = useState(false);
    const [toastMessage, setToastMessage] = useState("");
    const [error, setError] = useState("");
    const [isPending, setIsPending] = useState(false);

    // Message form state
    const [msgName, setMsgName] = useState("");
    const [msgEmail, setMsgEmail] = useState("");
    const [msgText, setMsgText] = useState("");
    const [msgPending, setMsgPending] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!agreed) {
            setError("Please agree to confirm notification consent.");
            return;
        }
        setError("");
        setIsPending(true);

        try {
            const { error: supabaseError } = await supabase
                .from('waitlist')
                .insert([{ email }]);

            if (supabaseError) {
                if (supabaseError.code === '23505') {
                    setSubmitted(true);
                    setShowToast(true);
                    return;
                }
                throw supabaseError;
            }
            setSubmitted(true);
            setShowToast(true);
            setToastMessage("You're on the list");
        } catch (err: any) {
            console.error(err);
            setError(err.message || "Failed to join. Please try again.");
        } finally {
            setIsPending(false);
        }
    };

    const handleMessageSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!msgName || !msgEmail || !msgText) return;

        setMsgPending(true);
        try {
            const { error: supabaseError } = await supabase
                .from('ms')
                .insert([{ name: msgName, email: msgEmail, message: msgText }]);

            if (supabaseError) {
                console.error("Supabase error:", supabaseError);
                setToastMessage("Failed to send message");
                setShowToast(true);
                return;
            }

            setMsgName("");
            setMsgEmail("");
            setMsgText("");
            setToastMessage("Message sent");
            setShowToast(true);
        } catch (err: any) {
            console.error("Error:", err);
            setToastMessage("Failed to send message");
            setShowToast(true);
        } finally {
            setMsgPending(false);
        }
    };

    useEffect(() => {
        if (showToast) {
            const timer = setTimeout(() => setShowToast(false), 5000);
            return () => clearTimeout(timer);
        }
    }, [showToast]);

    return (
        <div className="min-h-screen w-full bg-black text-white relative overflow-x-hidden">
            {/* Toast Notification */}
            <AnimatePresence>
                {showToast && (
                    <motion.div
                        initial={{ y: -100, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        exit={{ y: -100, opacity: 0 }}
                        transition={{ type: "spring", damping: 25, stiffness: 300 }}
                        className="fixed top-6 left-1/2 -translate-x-1/2 z-[100] w-full max-w-sm px-4"
                    >
                        <div className="bg-neutral-900 border border-white/10 rounded-2xl p-4 shadow-2xl backdrop-blur-xl flex items-start gap-3">
                            <div className="w-10 h-10 rounded-full bg-emerald-500/10 flex items-center justify-center shrink-0">
                                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-white font-medium text-sm">You're on the list</p>
                                <p className="text-neutral-400 text-xs mt-0.5 truncate">We'll reach out when the alpha is ready.</p>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Navbar */}
            <nav className="fixed top-0 w-full z-50 flex items-center justify-between px-6 py-4 bg-black/80 backdrop-blur-xl border-b border-white/5">
                <Link href="/" className="text-xl font-semibold tracking-tight">jars_</Link>
                <div />
            </nav>

            {/* Hero */}
            <div className="min-h-screen w-full bg-black flex flex-col items-center justify-center overflow-hidden relative pt-20">
                <div className="w-full absolute inset-0">
                    <SparklesCore
                        id="tsparticlesfullpage"
                        background="transparent"
                        minSize={0.3}
                        maxSize={0.8}
                        particleDensity={40}
                        className="w-full h-full"
                        particleColor="#FFFFFF"
                        speed={0.2}
                    />
                </div>

                <div className="relative z-20 text-center px-6 max-w-4xl mx-auto">
                    <h1
                        className="text-7xl sm:text-8xl md:text-9xl lg:text-[11rem] font-bold tracking-[-0.04em] text-white uppercase"
                        style={{ lineHeight: 0.85 }}
                    >
                        JARS
                    </h1>

                    <div className="mt-8 md:mt-10">
                        <p className="text-xl sm:text-2xl md:text-3xl text-neutral-400 font-light tracking-tight leading-relaxed">
                            <EncryptedText
                                text="Execution in milliseconds. Not minutes."
                                interval={35}
                                className="inline"
                            />
                        </p>
                    </div>

                    <div className="mt-12 flex flex-col items-center">
                        <div className="inline-block px-5 py-2.5 rounded-full border border-neutral-700 bg-neutral-900/50 text-neutral-300 text-sm font-medium tracking-wide">
                            Launch: March
                        </div>
                    </div>
                </div>

                <div className="absolute top-0 inset-x-0 bg-gradient-to-b from-black via-transparent to-transparent h-32 z-10" />
                <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black via-black/95 to-transparent h-48 z-10" />
            </div>

            {/* Waitlist Form */}
            <div className="w-full max-w-md mx-auto px-4 -mt-32 relative z-30 pb-24">
                <div className="bg-neutral-950 border border-white/10 p-8 rounded-2xl shadow-2xl">
                    {!submitted ? (
                        <form onSubmit={handleSubmit} className="space-y-6">
                            <div className="space-y-3 text-center">
                                <h2 className="text-2xl font-semibold tracking-tight">Get Early Access</h2>
                                <p className="text-neutral-500 text-base leading-relaxed">
                                    Join the waitlist. Limited spots.
                                </p>
                            </div>

                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="email" className="text-neutral-500 text-xs uppercase tracking-widest">Email</Label>
                                    <Input
                                        id="email"
                                        type="email"
                                        placeholder="you@example.com"
                                        className="bg-black/80 border-white/10 focus:border-neutral-500 transition-all h-12 text-base"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        required
                                    />
                                </div>

                                <div className="flex items-start gap-3 p-4 rounded-xl border border-white/5 bg-white/[0.02]">
                                    <Checkbox
                                        id="notify"
                                        checked={agreed}
                                        onCheckedChange={(c) => setAgreed(c as boolean)}
                                        className="mt-0.5"
                                    />
                                    <div className="grid gap-1.5 leading-none">
                                        <Label htmlFor="notify" className="text-sm font-medium cursor-pointer">
                                            Keep me updated
                                        </Label>
                                        <p className="text-xs text-neutral-500 leading-relaxed">
                                            Receive engineering updates and access invitations.
                                        </p>
                                    </div>
                                </div>

                                {error && <p className="text-red-400 text-xs text-center">{error}</p>}
                            </div>

                            <Button
                                type="submit"
                                disabled={isPending}
                                className="w-full bg-white text-black hover:bg-neutral-200 font-medium h-12 text-base"
                            >
                                {isPending ? <Loader2 className="animate-spin w-5 h-5" /> : "Request Access"}
                            </Button>
                        </form>
                    ) : (
                        <div className="text-center space-y-4 py-6">
                            <div className="w-16 h-16 bg-emerald-500/10 text-emerald-400 rounded-full flex items-center justify-center mx-auto border border-emerald-500/20">
                                <CheckCircle2 className="w-7 h-7" />
                            </div>
                            <h2 className="text-2xl font-semibold text-white">You're in.</h2>
                            <p className="text-neutral-400 text-base max-w-xs mx-auto leading-relaxed">
                                We'll be in touch when the alpha is ready.
                            </p>
                            <div className="pt-2">
                                <Button variant="ghost" className="text-neutral-500 hover:text-white text-sm" onClick={() => { setSubmitted(false); setEmail(""); }}>
                                    Add another email
                                </Button>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Engineering Section */}
            <section className="py-28 px-6 border-t border-white/5 bg-neutral-950">
                <div className="max-w-5xl mx-auto">
                    <div className="flex items-center gap-3 mb-14">
                        <Terminal className="w-5 h-5 text-neutral-400" />
                        <h2 className="text-2xl font-semibold tracking-tight">Under the Hood and stuff</h2>
                    </div>

                    <div className="grid lg:grid-cols-2 gap-16">
                        <div className="space-y-8">
                            <div>
                                <h3 className="text-xl font-medium text-white mb-4">Event-Driven Pipeline</h3>
                                <p className="text-neutral-400 text-lg leading-relaxed">
                                    The core is a pub/sub architecture. WebSocket connections maintain persistent streams to exchange APIs. Incoming signals hit a message queue, get fanned out to worker processes, and execute in parallel. State is reconciled against the exchange on every cycle.
                                </p>
                            </div>

                            <div>
                                <h4 className="text-sm font-medium text-neutral-400 mb-4 uppercase tracking-widest">Signal Flow</h4>
                                <div className="flex flex-wrap items-center gap-3 text-sm font-mono">
                                    <span className="px-4 py-2 rounded-lg bg-neutral-900 text-neutral-300 border border-white/5">Ingestion</span>
                                    <span className="text-neutral-600">→</span>
                                    <span className="px-4 py-2 rounded-lg bg-neutral-900 text-neutral-300 border border-white/5">Buffer</span>
                                    <span className="text-neutral-600">→</span>
                                    <span className="px-4 py-2 rounded-lg bg-neutral-900 text-neutral-300 border border-white/5">Fan-Out</span>
                                    <span className="text-neutral-600">→</span>
                                    <span className="px-4 py-2 rounded-lg bg-neutral-900 text-neutral-300 border border-white/5">Settlement</span>
                                </div>
                            </div>

                            <div>
                                <h4 className="text-sm font-medium text-neutral-400 mb-4 uppercase tracking-widest">Design Principles</h4>
                                <ul className="space-y-4 text-neutral-400 text-lg">
                                    <li className="flex items-start gap-3">
                                        <span className="w-1.5 h-1.5 rounded-full bg-neutral-500 mt-2.5 shrink-0" />
                                        <span><strong className="text-white font-medium">Atomic Locking</strong> — Balance calculations locked at the process level. No race conditions.</span>
                                    </li>
                                    <li className="flex items-start gap-3">
                                        <span className="w-1.5 h-1.5 rounded-full bg-neutral-500 mt-2.5 shrink-0" />
                                        <span><strong className="text-white font-medium">Idempotent Execution</strong> — Every order carries a unique identifier. Retries can't create duplicates.</span>
                                    </li>
                                    <li className="flex items-start gap-3">
                                        <span className="w-1.5 h-1.5 rounded-full bg-neutral-500 mt-2.5 shrink-0" />
                                        <span><strong className="text-white font-medium">Continuous Reconciliation</strong> — Background verification against exchange state.</span>
                                    </li>
                                </ul>
                            </div>
                        </div>

                        {/* Terminal */}
                        <div className="bg-[#0c0c0c] border border-neutral-800 rounded-xl overflow-hidden font-mono text-[13px] shadow-2xl">
                            <div className="flex items-center gap-2 px-4 py-3 bg-neutral-900 border-b border-neutral-800">
                                <div className="flex gap-2">
                                    <div className="w-3 h-3 rounded-full bg-neutral-700" />
                                    <div className="w-3 h-3 rounded-full bg-neutral-700" />
                                    <div className="w-3 h-3 rounded-full bg-neutral-700" />
                                </div>
                                <span className="ml-4 text-neutral-500 text-xs font-medium">jars-engine — bash — 120×34</span>
                            </div>
                            <div className="p-5 space-y-0.5 text-[12px] leading-relaxed overflow-x-auto text-neutral-400">
                                <p className="text-neutral-300">user@jars-prod:~$ ./engine --mode=live --workers=24</p>
                                <p className="text-neutral-500 mt-3">[2026-03-12 04:21:33.847Z] [INFO] Engine v3.2.1 starting...</p>
                                <p className="text-neutral-500">[2026-03-12 04:21:33.849Z] [INFO] Connecting to wss://stream.bybit.com/v5/private</p>
                                <p className="text-neutral-500">[2026-03-12 04:21:33.851Z] [INFO] WebSocket handshake complete (4ms)</p>
                                <p className="text-neutral-500">[2026-03-12 04:21:33.852Z] [INFO] Spawning 24 worker processes</p>
                                <p className="text-neutral-500">[2026-03-12 04:21:33.890Z] [INFO] All workers ready. Listening for signals...</p>
                                <p className="text-neutral-500 mt-2">[2026-03-12 04:21:34.102Z] [DEBUG] Acquired lock: balance_mutex:8a2f91c</p>
                                <p className="text-neutral-300">[2026-03-12 04:21:34.104Z] [SIGNAL] BTC-USDT LONG @ 97284.50 | qty: 0.4200 | seq: 2941827</p>
                                <p className="text-neutral-500">[2026-03-12 04:21:34.106Z] [INFO] Broadcasting to 142 subscribers...</p>
                                <p className="text-neutral-500">[2026-03-12 04:21:34.142Z] [INFO] 142/142 orders dispatched</p>
                                <p className="text-neutral-500">[2026-03-12 04:21:34.144Z] [INFO] Avg latency: 38ms | Max: 67ms | Failures: 0</p>
                                <p className="text-neutral-500">[2026-03-12 04:21:34.146Z] [DEBUG] Released lock: balance_mutex:8a2f91c</p>
                                <p className="text-neutral-300">[2026-03-12 04:21:34.148Z] [ACK] All orders confirmed by exchange</p>
                                <p className="text-neutral-500">[2026-03-12 04:21:34.150Z] [INFO] Ledger entries committed: txn_9f84a7b2</p>
                                <p className="text-neutral-500 mt-2">[2026-03-12 04:21:34.152Z] [INFO] Awaiting next signal...</p>
                                <div className="flex items-center mt-2">
                                    <span className="text-neutral-300">user@jars-prod:~$</span>
                                    <div className="animate-pulse bg-neutral-400 h-4 w-2 ml-2" />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Roadmap */}
            <div className="bg-black text-white w-full">
                <Timeline data={[
                    {
                        title: "Phase 1: Foundation",
                        content: (
                            <div>
                                <p className="text-neutral-300 text-lg leading-relaxed mb-6">
                                    The immutable ledger. A double-entry accounting system where every transaction fees, profits, losses is tracked with decimal precision. No floating point. No ambiguity. Every satoshi accounted for.
                                </p>
                                <div className="grid grid-cols-2 gap-3">
                                    <div className="rounded-lg bg-neutral-900/50 p-4 border border-white/5">
                                        <h4 className="text-white text-xs font-medium uppercase tracking-wider mb-2">Identity Layer</h4>
                                        <div className="h-1.5 w-full bg-neutral-800 rounded-full"><div className="h-full w-full bg-neutral-400 rounded-full" /></div>
                                    </div>
                                    <div className="rounded-lg bg-neutral-900/50 p-4 border border-white/5">
                                        <h4 className="text-white text-xs font-medium uppercase tracking-wider mb-2">Ledger Engine</h4>
                                        <div className="h-1.5 w-full bg-neutral-800 rounded-full"><div className="h-full w-full bg-neutral-400 rounded-full" /></div>
                                    </div>
                                </div>
                            </div>
                        ),
                    },
                    {
                        title: "Phase 2: Connectivity",
                        content: (
                            <div>
                                <p className="text-neutral-300 text-lg leading-relaxed mb-6">
                                    The real time fabric. Persistent connections to exchange matching engines. Proprietary event buffers. Distributed locking that eliminates the race conditions plaguing amateur systems.
                                </p>
                                <div className="space-y-2.5">
                                    <div className="flex items-center gap-3 text-base text-neutral-400">
                                        <div className="w-2 h-2 rounded-full bg-neutral-400" />
                                        <span>Distributed Lock Manager — Complete</span>
                                    </div>
                                    <div className="flex items-center gap-3 text-base text-neutral-400">
                                        <div className="w-2 h-2 rounded-full bg-neutral-400" />
                                        <span>Low-Latency Socket Layer — Complete</span>
                                    </div>
                                    <div className="flex items-center gap-3 text-base text-neutral-400">
                                        <div className="w-2 h-2 rounded-full bg-neutral-500 animate-pulse" />
                                        <span>Parallel Execution Engine — Sigh, In progress</span>
                                    </div>
                                </div>
                            </div>
                        ),
                    },
                    {
                        title: "Phase 3: Alpha",
                        content: (
                            <div>
                                <p className="text-neutral-300 text-lg leading-relaxed mb-4">
                                    Controlled deployment with early users. Stress-testing order routing against live volatility. Measuring slippage. Hardening reconciliation. Real capital. Real speed.
                                </p>
                                <div className="p-4 bg-neutral-900/50 border border-neutral-800 rounded-lg">
                                    <p className="text-neutral-300 text-base font-medium">Target: Sub-50ms execution latency at scale.</p>
                                </div>
                            </div>
                        ),
                    },
                ]} />
            </div>

            {/* Questions */}
            <section className="py-28 px-6 bg-neutral-950 border-t border-white/5">
                <div className="max-w-lg mx-auto text-center">
                    <h2 className="text-2xl font-semibold text-white mb-3">Curious about the architecture?</h2>
                    <p className="text-neutral-500 text-lg mb-4">I reply/read every message personally.</p>
                    <div className="flex items-center justify-center gap-4 mb-12">
                        <a href="https://x.com/astrovinee" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-neutral-400 hover:text-white transition-colors">
                            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                            </svg>
                            <span className="text-sm">@astrovinee</span>
                        </a>
                        <span className="text-neutral-700">•</span>
                        <a href="https://github.com/astrovine" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-neutral-400 hover:text-white transition-colors">
                            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                            </svg>
                            <span className="text-sm">astrovine</span>
                        </a>
                    </div>

                    <form onSubmit={handleMessageSubmit} className="space-y-4 text-left">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="q-name" className="text-neutral-500 text-xs uppercase tracking-widest">Name</Label>
                                <Input
                                    id="q-name"
                                    placeholder="Your name"
                                    className="bg-black/80 border-white/10 h-12 text-base"
                                    value={msgName}
                                    onChange={(e) => setMsgName(e.target.value)}
                                    required
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="q-email" className="text-neutral-500 text-xs uppercase tracking-widest">Email</Label>
                                <Input
                                    id="q-email"
                                    type="email"
                                    placeholder="you@example.com"
                                    className="bg-black/80 border-white/10 h-12 text-base"
                                    value={msgEmail}
                                    onChange={(e) => setMsgEmail(e.target.value)}
                                    required
                                />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="q-message" className="text-neutral-500 text-xs uppercase tracking-widest">Your Question</Label>
                            <textarea
                                id="q-message"
                                className="flex min-h-[140px] w-full rounded-xl border border-white/10 bg-black/80 px-4 py-3 text-base text-white placeholder:text-neutral-600 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-neutral-500 resize-none"
                                placeholder="How do you prevent order failures during high volatility?"
                                value={msgText}
                                onChange={(e) => setMsgText(e.target.value)}
                                required
                            />
                        </div>
                        <Button
                            type="submit"
                            disabled={msgPending}
                            className="w-full bg-white/5 hover:bg-white/10 text-white font-medium h-12 text-base border border-white/10"
                        >
                            {msgPending ? <Loader2 className="animate-spin w-4 h-4 mr-2" /> : <Send className="w-4 h-4 mr-2" />}
                            {msgPending ? "Sending..." : "Send Message"}
                        </Button>
                    </form>
                </div>
            </section>

            {/* Africa Section */}
            <section className="py-24 px-6 bg-black border-t border-white/5 relative overflow-hidden">
                <div className="max-w-4xl mx-auto text-center relative z-20">
                    <h2 className="text-3xl md:text-5xl font-bold text-white mb-6 tracking-tight">
                        Building the next generation of<br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-sky-400">capital infrastructure</span> for Africa
                    </h2>
                    <p className="text-neutral-400 text-lg max-w-2xl mx-auto mb-8">
                        From Lagos to Nairobi to Johannesburg.Anywhere.Everywhere
                    </p>
                </div>

                <div className="w-full max-w-2xl mx-auto h-40 relative">
                    {/* Gradient lines */}
                    <div className="absolute inset-x-20 top-0 bg-gradient-to-r from-transparent via-emerald-500 to-transparent h-[2px] w-3/4 blur-sm" />
                    <div className="absolute inset-x-20 top-0 bg-gradient-to-r from-transparent via-emerald-500 to-transparent h-px w-3/4" />
                    <div className="absolute inset-x-60 top-0 bg-gradient-to-r from-transparent via-sky-500 to-transparent h-[5px] w-1/4 blur-sm" />
                    <div className="absolute inset-x-60 top-0 bg-gradient-to-r from-transparent via-sky-500 to-transparent h-px w-1/4" />

                    <SparklesCore
                        background="transparent"
                        minSize={0.4}
                        maxSize={1}
                        particleDensity={800}
                        className="w-full h-full"
                        particleColor="#FFFFFF"
                    />

                    <div className="absolute inset-0 w-full h-full bg-black [mask-image:radial-gradient(350px_200px_at_top,transparent_20%,white)]" />
                </div>
            </section>

            <footer className="py-12 text-center text-neutral-600 text-xs bg-black border-t border-white/5">
                <p>© 2026 JARS Systems. All rights reserved.</p>
            </footer>
        </div>
    );
}
