"use client";

import React, { useEffect, useState, useRef } from "react";
import { Terminal } from "lucide-react";
import { cn } from "@/lib/utils";

// Types for our terminal steps
type TerminalStep = {
    type: "command" | "output" | "splash" | "input_prompt";
    content?: string;
    delay?: number; // Time to wait before showing this step
    typingSpeed?: number; // For commands
    style?: string; // Color/style class
};

const SPLASH_ART = `
      ██╗ █████╗ ██████╗ ███████╗
      ██║██╔══██╗██╔══██╗██╔════╝
      ██║███████║██████╔╝███████╗
 ██   ██║██╔══██║██╔══██╗╚════██║
 ╚█████╔╝██║  ██║██║  ██║███████║
  ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝
`;

const INITIAL_STEPS: TerminalStep[] = [
    // 1. Splash Screen
    { type: "splash", content: SPLASH_ART, delay: 200 },
    { type: "output", content: "What are we trading today?", style: "text-emerald-500 font-bold text-center mt-2", delay: 100 },
    { type: "output", content: "Initializing secure automated environment...", style: "text-white/40 text-center mb-6", delay: 300 },
    
    // 2. Login Flow
    { type: "input_prompt", content: "Authentication Required", delay: 500 },
    { type: "command", content: "auth login", delay: 800 },
    { type: "output", content: "• Signing in as demo@jars.fi...", style: "text-white/60", delay: 400 },
    { type: "output", content: "✓ Session Authenticated [2FA Verified]", style: "text-emerald-400 font-bold", delay: 600 },

    // 3. The "Profound" Action: Following a trader
    { type: "command", content: "subs follow --alias 'Quantum_X' --alloc 5000", delay: 1000 },
    
    // 4. The "Thread of Tough Process" - Execution Logs
    { type: "output", content: "[SYS] Initializing copy protocol for 'Quantum_X'...", style: "text-blue-400", delay: 200 },
    { type: "output", content: "[NET] Establishing persistent WebSocket -> wss://api.jars.fi/v2/stream", style: "text-white/50", delay: 100 },
    { type: "output", content: "[NET] Connection established. Latency: 14ms", style: "text-white/50", delay: 150 },
    { type: "output", content: "[RISK] Verifying margin requirements for $5,000.00 allocation...", style: "text-white/50", delay: 200 },
    { type: "output", content: "[RISK] Check passed. Leverage cap: 5x.", style: "text-emerald-500/80", delay: 100 },
    
    { type: "output", content: "[SYNC] Fetching master open positions...", style: "text-white/50", delay: 400 },
    { type: "output", content: "Detected 2 active positions:", style: "text-white underline mt-2", delay: 100 },
    { 
        type: "output", 
        content: "  • LONG BTC/USDT @ 64,210.50 (Size: 0.42 BTC)", 
        style: "text-emerald-400 ml-4", 
        delay: 200 
    },
    { 
        type: "output", 
        content: "  • SHORT ETH/USDT @ 3,450.20 (Size: 5.10 ETH)", 
        style: "text-red-400 ml-4 mb-2", 
        delay: 200 
    },

    { type: "output", content: "[EXEC] Calculating entry parity...", style: "text-white/50", delay: 300 },
    { type: "output", content: "[ALGO] Slippage tolerance set to 0.1%. Mode: AGGRESSIVE.", style: "text-yellow-500/80", delay: 200 },
    
    { type: "output", content: "[ORDER] SUBMIT MARKET BUY BTC/USDT...", style: "text-white", delay: 100 },
    { type: "output", content: ">>> FILL: 0.02 BTC @ 64,212.00 (Diff: +1.50)", style: "text-emerald-500 font-bold", delay: 200 },
    
    { type: "output", content: "[ORDER] SUBMIT MARKET SELL ETH/USDT...", style: "text-white", delay: 100 },
    { type: "output", content: ">>> FILL: 0.25 ETH @ 3,449.80 (Diff: -0.40)", style: "text-emerald-500 font-bold", delay: 200 },

    { type: "output", content: "[INFO] Synchronization Complete.", style: "text-blue-400 mt-2", delay: 500 },
    { type: "output", content: "Sentinel Active. Listening for real-time signals...", style: "text-emerald-400 animate-pulse", delay: 1000 },
    
    // 5. Live "Heartbeat" logs
    { type: "output", content: "[Ping] 14ms...", style: "text-white/20 text-xs", delay: 2000 },
    { type: "output", content: "[Ping] 15ms...", style: "text-white/20 text-xs", delay: 2000 },
    { type: "output", content: "[Ping] 13ms...", style: "text-white/20 text-xs", delay: 2000 },
];

export function TerminalDemo() {
    const [lines, setLines] = useState<any[]>([]);
    const [stepIndex, setStepIndex] = useState(0);
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        let timeoutId: NodeJS.Timeout;

        const processStep = async () => {
            if (stepIndex >= INITIAL_STEPS.length) {
                // Loop or stop
                // setTimeout(() => {
                //    setLines([]);
                //    setStepIndex(0);
                // }, 5000);
                return;
            }

            const step = INITIAL_STEPS[stepIndex];

            // Initial delay for the step
            await new Promise(r => setTimeout(r, step.delay || 0));

            if (step.type === "splash") {
                setLines(prev => [...prev, { type: "splash", content: step.content }]);
                setStepIndex(prev => prev + 1);
            }
            else if (step.type === "command") {
                // Simulate typing
                const chars = step.content?.split("") || [];
                let currentText = "";

                // Add a line for the command prompt
                const promptId = Date.now();
                setLines(prev => [...prev, { type: "prompt", id: promptId, content: "" }]);

                for (let i = 0; i < chars.length; i++) {
                    await new Promise(r => setTimeout(r, step.typingSpeed || 50 + Math.random() * 30));
                    currentText += chars[i];
                    setLines(prev => prev.map(line =>
                        line.id === promptId ? { ...line, content: currentText } : line
                    ));
                }
                setStepIndex(prev => prev + 1);
            }
            else if (step.type === "output" || step.type === "input_prompt") {
                setLines(prev => [...prev, { type: step.type, content: step.content, style: step.style }]);
                setStepIndex(prev => prev + 1);
            }
        };

        processStep();

        return () => clearTimeout(timeoutId);
    }, [stepIndex]);

    // Auto-scroll
    useEffect(() => {
        if (containerRef.current) {
            containerRef.current.scrollTop = containerRef.current.scrollHeight;
        }
    }, [lines]);

    return (
        <div className="w-full max-w-5xl mx-auto rounded-xl border border-white/10 bg-[#0a0a0a] shadow-2xl overflow-hidden font-mono text-sm md:text-base">
            {/* Title Bar */}
            <div className="flex items-center justify-between px-4 py-3 bg-[#111] border-b border-white/5">
                <div className="flex items-center gap-2">
                    <div className="flex gap-1.5">
                        <div className="w-3 h-3 rounded-full bg-red-500/80" />
                        <div className="w-3 h-3 rounded-full bg-amber-500/80" />
                        <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
                    </div>
                    <div className="ml-3 flex items-center gap-2 text-xs text-white/40">
                        <Terminal size={12} />
                        <span>jars-cli — v2.0.1</span>
                    </div>
                </div>
                <div className="text-xs text-white/20">bash</div>
            </div>

            {/* Terminal Viewport */}
            <div
                ref={containerRef}
                className="h-[500px] md:h-[600px] overflow-y-auto p-4 md:p-6 space-y-1 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent"
            >
                {lines.map((line, i) => (
                    <div key={i} className={cn("break-words", line.type === "prompt" ? "flex items-start gap-2" : "")}>
                        {line.type === "splash" && (
                            <pre className="text-emerald-500 font-black leading-none text-[8px] md:text-sm whitespace-pre-wrap select-none text-center">
                                {line.content}
                            </pre>
                        )}

                        {line.type === "prompt" && (
                            <>
                                <span className="text-emerald-500 font-bold shrink-0">➜</span>
                                <span className="text-white">{line.content}</span>
                            </>
                        )}

                        {line.type === "output" && (
                            <div className={cn("text-white/80", line.style)}>{line.content}</div>
                        )}

                        {line.type === "input_prompt" && (
                            <div className="mt-8 text-center animate-pulse text-white font-bold">{line.content}</div>
                        )}
                    </div>
                ))}
                <div ref={containerRef} />
            </div>
        </div>
    );
}
