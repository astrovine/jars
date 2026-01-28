"use client";

import React, { useEffect, useState, useRef, useCallback } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  ArrowRight,
  CheckCircle,
  Check,
  Shield,
  Zap,
  Lock,
  Terminal,
  Globe,
  Eye,
  BarChart3,
  TrendingUp,
  ChevronDown,
  Users,
  Clock,
  Target,
  Award,
  Star,
  Radio,
  Server,
  Cpu,
  Activity,
  BadgeCheck,
  Sparkles,
  Github,
  Twitter,
  Copy,
  Terminal as TerminalIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ContainerScroll } from "@/components/ui/container-scroll-animation";
import { WobbleCard } from "@/components/ui/wobble-card";
import { Spotlight } from "@/components/ui/spotlight";
import { SparklesCore } from "@/components/ui/sparkles";
import { motion, useScroll, useTransform, AnimatePresence, useMotionValue, useSpring } from "framer-motion";
import dynamic from "next/dynamic";
import { FocusCards } from "@/components/ui/focus-cards";
import { PointerHighlight } from "@/components/ui/pointer-highlight";
import { CookieConsent } from "@/components/cookie-consent";
import { InfiniteMovingCards } from "@/components/ui/infinite-moving-cards";
import { TextHoverEffect } from "@/components/ui/text-hover-effect";
import WorldMap from "@/components/ui/world-map";
import { TerminalDemo } from "@/components/terminal-demo";

const World = dynamic(() => import("@/components/ui/globe").then((m) => m.World), {
  ssr: false,
});

const CRYPTO_LOGOS = [
  { symbol: "BTC", name: "Bitcoin", src: "https://cryptologos.cc/logos/bitcoin-btc-logo.svg?v=035" },
  { symbol: "ETH", name: "Ethereum", src: "https://cryptologos.cc/logos/ethereum-eth-logo.svg?v=035" },
  { symbol: "SOL", name: "Solana", src: "https://cryptologos.cc/logos/solana-sol-logo.svg?v=035" },
  { symbol: "USDT", name: "Tether", src: "https://cryptologos.cc/logos/tether-usdt-logo.svg?v=035" },
  { symbol: "BNB", name: "BNB Chain", src: "https://cryptologos.cc/logos/bnb-bnb-logo.svg?v=035" },
  { symbol: "XRP", name: "XRP", src: "https://cryptologos.cc/logos/xrp-xrp-logo.svg?v=035" },
  { symbol: "USDC", name: "USDC", src: "https://cryptologos.cc/logos/usd-coin-usdc-logo.svg?v=035" },
  { symbol: "ADA", name: "Cardano", src: "https://cryptologos.cc/logos/cardano-ada-logo.svg?v=035" },
  { symbol: "AVAX", name: "Avalanche", src: "https://cryptologos.cc/logos/avalanche-avax-logo.svg?v=035" },
  { symbol: "DOGE", name: "Dogecoin", src: "https://cryptologos.cc/logos/dogecoin-doge-logo.svg?v=035" },
];


function AnimatedNumber({ value, prefix = "", suffix = "", className = "" }: {
  value: number | string;
  prefix?: string;
  suffix?: string;
  className?: string;
}) {
  const [displayValue, setDisplayValue] = useState(value);

  useEffect(() => {
    setDisplayValue(value);
  }, [value]);

  return (
    <span className={cn("inline-flex items-baseline tabular-nums", className)}>
      {prefix}
      <AnimatePresence mode="popLayout">
        <motion.span
          key={displayValue.toString()}
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: -20, opacity: 0 }}
          transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
        >
          {displayValue}
        </motion.span>
      </AnimatePresence>
      {suffix}
    </span>
  );
}


function RotatingWords({
  words,
  interval = 5000,
  className = ""
}: {
  words: string[];
  interval?: number;
  className?: string;
}) {
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % words.length);
    }, interval);
    return () => clearInterval(timer);
  }, [words.length, interval]);

  return (
    <span className={cn("inline-block relative", className)}>
      <AnimatePresence mode="wait">
        <motion.span
          key={currentIndex}
          initial={{ opacity: 0, y: 20, filter: "blur(8px)" }}
          animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
          exit={{ opacity: 0, y: -20, filter: "blur(8px)" }}
          transition={{
            duration: 0.6,
            ease: [0.25, 0.46, 0.45, 0.94]
          }}
          className="inline-block"
        >
          {words[currentIndex]}
        </motion.span>
      </AnimatePresence>
    </span>
  );
}


function TypewriterText({
  phrases,
  typingSpeed = 50,
  deletingSpeed = 30,
  pauseDuration = 3000,
  className = ""
}: {
  phrases: string[];
  typingSpeed?: number;
  deletingSpeed?: number;
  pauseDuration?: number;
  className?: string;
}) {
  const [currentPhraseIndex, setCurrentPhraseIndex] = useState(0);
  const [displayText, setDisplayText] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    const currentPhrase = phrases[currentPhraseIndex];

    if (isPaused) {
      const pauseTimer = setTimeout(() => {
        setIsPaused(false);
        setIsDeleting(true);
      }, pauseDuration);
      return () => clearTimeout(pauseTimer);
    }

    if (isDeleting) {
      if (displayText === "") {
        setIsDeleting(false);
        setCurrentPhraseIndex((prev) => (prev + 1) % phrases.length);
      } else {
        const deleteTimer = setTimeout(() => {
          setDisplayText(displayText.slice(0, -1));
        }, deletingSpeed);
        return () => clearTimeout(deleteTimer);
      }
    } else {
      if (displayText === currentPhrase) {
        setIsPaused(true);
      } else {
        const typeTimer = setTimeout(() => {
          setDisplayText(currentPhrase.slice(0, displayText.length + 1));
        }, typingSpeed);
        return () => clearTimeout(typeTimer);
      }
    }
  }, [displayText, isDeleting, isPaused, currentPhraseIndex, phrases, typingSpeed, deletingSpeed, pauseDuration]);

  return (
    <span className={cn("inline", className)}>
      {displayText}
      <motion.span
        animate={{ opacity: [1, 0] }}
        transition={{ duration: 0.5, repeat: Infinity, repeatType: "reverse" }}
        className="inline-block w-[2px] h-[1em] bg-white/40 ml-0.5 align-middle"
      />
    </span>
  );
}


function SpotlightCard({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  const cardRef = useRef<HTMLDivElement>(null);
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    mouseX.set(e.clientX - rect.left);
    mouseY.set(e.clientY - rect.top);
  }, [mouseX, mouseY]);

  return (
    <motion.div
      ref={cardRef}
      className={cn("relative rounded-2xl overflow-hidden", className)}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        background: "rgba(10, 10, 10, 0.6)",
        border: "1px solid rgba(255, 255, 255, 0.05)",
      }}
    >
      {/* Spotlight gradient */}
      <motion.div
        className="pointer-events-none absolute inset-0"
        style={{
          background: `radial-gradient(600px circle at ${mouseX.get()}px ${mouseY.get()}px, rgba(16, 185, 129, 0.06), transparent 40%)`,
          opacity: isHovered ? 1 : 0,
        }}
      />
      {/* Border glow */}
      <motion.div
        className="pointer-events-none absolute inset-0 rounded-2xl"
        style={{
          background: `radial-gradient(400px circle at ${mouseX.get()}px ${mouseY.get()}px, rgba(16, 185, 129, 0.15), transparent 40%)`,
          opacity: isHovered ? 1 : 0,
          mask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
          maskComposite: "exclude",
          padding: "1px",
        }}
      />
      {children}
    </motion.div>
  );
}


function CryptoMarquee() {
  return (
    <div className="relative w-full overflow-hidden py-10 bg-[#020202] border-y border-white/5">
      {/* Side Fades for Depth */}
      <div className="absolute left-0 top-0 bottom-0 w-40 bg-gradient-to-r from-[#020202] to-transparent z-10" />
      <div className="absolute right-0 top-0 bottom-0 w-40 bg-gradient-to-l from-[#020202] to-transparent z-10" />

      <div className="flex animate-marquee items-center">
        {/* Triple duplication for super smooth infinite loop */}
        {[...CRYPTO_LOGOS, ...CRYPTO_LOGOS, ...CRYPTO_LOGOS].map((crypto, i) => (
          <div key={`${crypto.symbol}-${i}`} className="flex items-center gap-3 mx-8 flex-shrink-0 group cursor-default">
            {/* The Logo */}
            <div className="w-10 h-10 flex items-center justify-center grayscale opacity-40 group-hover:grayscale-0 group-hover:opacity-100 transition-all duration-300 transform group-hover:scale-110">
              <img src={crypto.src} alt={crypto.name} className="w-8 h-8" />
            </div>

            {/* The Text */}
            <div className="flex flex-col">
              <span className="text-sm font-semibold text-white/40 group-hover:text-white transition-colors">
                {crypto.name}
              </span>
              <span className="text-[10px] font-mono text-white/20 group-hover:text-emerald-400 transition-colors">
                {crypto.symbol}-PERP
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}


// Custom professional SVG icons for fintech trust
const SignalPulseIcon = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M2 12h2" />
    <path d="M6 12a6 6 0 0 1 6-6" />
    <path d="M6 12a6 6 0 0 0 6 6" />
    <path d="M9 12a3 3 0 0 1 3-3" />
    <path d="M9 12a3 3 0 0 0 3 3" />
    <circle cx="12" cy="12" r="1" fill="currentColor" />
    <path d="M12 12h10" />
  </svg>
);

const NetworkNodesIcon = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="5" r="2" />
    <circle cx="5" cy="19" r="2" />
    <circle cx="19" cy="19" r="2" />
    <path d="M12 7v4" />
    <path d="M12 11L5 17" />
    <path d="M12 11l7 6" />
    <circle cx="12" cy="12" r="1" fill="currentColor" />
  </svg>
);

const OrderExecuteIcon = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="18" height="18" rx="2" />
    <path d="M3 9h18" />
    <path d="M9 3v6" />
    <path d="M9 14l2 2 4-4" />
  </svg>
);

function InfrastructureSection() {
  return (
    <section id="infrastructure" className="py-32 bg-[#020202] relative">
      <div className="max-w-7xl mx-auto px-6">
        <div className="mb-16 max-w-3xl">
          <h2 className="text-5xl lg:text-7xl font-semibold tracking-tighter mb-6">
            Signal to execution <span className="text-white/20">instantly.</span>
          </h2>
          <p className="text-xl text-white/50 font-light leading-relaxed">
            Our Sentinel engine monitors master traders. You copy them in milliseconds.
            No complexity. Just results.
          </p>
        </div>

        {/* WobbleCard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 w-full">
          {/* Card 1: Signal Detected - Spans 2 columns */}
          <WobbleCard
            containerClassName="col-span-1 lg:col-span-2 h-full bg-[#0a0a0c] border border-white/[0.04] min-h-[400px] lg:min-h-[350px]"
          >
            <div className="max-w-md relative z-10">
              <div className="w-12 h-12 rounded-xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center mb-6">
                <SignalPulseIcon className="w-6 h-6 text-white/70" />
              </div>
              <h3 className="text-left text-balance text-2xl lg:text-3xl font-semibold tracking-tight text-white mb-4">
                1. Signal Detected
              </h3>
              <p className="text-left text-base/6 text-white/40">
                We monitor top traders 24/7. The moment they open a trade on Binance or Bybit, our Sentinel engine captures the data packet in under 10ms.
              </p>
            </div>
            {/* Background decorative element */}
            <div className="absolute -right-20 lg:-right-10 -bottom-20 w-64 h-64 opacity-[0.02] pointer-events-none">
              <svg viewBox="0 0 100 100" fill="none" stroke="currentColor" strokeWidth="0.5" className="w-full h-full text-white">
                <circle cx="50" cy="50" r="10" />
                <circle cx="50" cy="50" r="20" />
                <circle cx="50" cy="50" r="30" />
                <circle cx="50" cy="50" r="40" />
                <line x1="50" y1="50" x2="90" y2="50" />
              </svg>
            </div>
          </WobbleCard>

          {/* Card 2: Parallel Broadcast - Single column */}
          <WobbleCard
            containerClassName="col-span-1 min-h-[350px] bg-[#0a0a0c] border border-white/[0.04]"
          >
            <div className="relative z-10">
              <div className="w-12 h-12 rounded-xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center mb-6">
                <NetworkNodesIcon className="w-6 h-6 text-white/70" />
              </div>
              <h3 className="max-w-80 text-left text-balance text-2xl lg:text-3xl font-semibold tracking-tight text-white mb-4">
                2. Parallel Broadcast
              </h3>
              <p className="max-w-[26rem] text-left text-base/6 text-white/40">
                The signal is verified and broadcast to all copiers simultaneously. Zero queue times. Zero delays.
              </p>
            </div>
            {/* Background decorative element */}
            <div className="absolute -right-8 -bottom-8 w-40 h-40 opacity-[0.02] pointer-events-none">
              <svg viewBox="0 0 100 100" fill="none" stroke="currentColor" strokeWidth="0.8" className="w-full h-full text-white">
                <circle cx="50" cy="20" r="8" />
                <circle cx="20" cy="80" r="8" />
                <circle cx="80" cy="80" r="8" />
                <line x1="50" y1="28" x2="50" y2="50" />
                <line x1="50" y1="50" x2="24" y2="74" />
                <line x1="50" y1="50" x2="76" y2="74" />
                <circle cx="50" cy="50" r="4" fill="currentColor" />
              </svg>
            </div>
          </WobbleCard>

          {/* Card 3: Instant Execution - Spans full width */}
          <WobbleCard
            containerClassName="col-span-1 lg:col-span-3 bg-[#0a0a0c] border border-white/[0.04] min-h-[400px] lg:min-h-[280px]"
          >
            <div className="max-w-lg relative z-10">
              <div className="w-12 h-12 rounded-xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center mb-6">
                <OrderExecuteIcon className="w-6 h-6 text-white/70" />
              </div>
              <h3 className="max-w-sm md:max-w-lg text-left text-balance text-2xl lg:text-3xl font-semibold tracking-tight text-white mb-4">
                3. Instant Execution
              </h3>
              <p className="max-w-[32rem] text-left text-base/6 text-white/40">
                Orders are placed directly in your exchange account via API. You get the same entry price as the master trader. Non-custodialâ€”your funds never leave your account.
              </p>
              <div className="flex items-center gap-6 mt-6">
                <div className="flex items-center gap-2">
                  {/*<div className="w-1.5 h-1.5 rounded-full bg-emerald-500/70" />*/}
                  <span className="text-sm text-white/40">&lt;50ms Latency</span>
                </div>
                <div className="flex items-center gap-2">
                  {/*<div className="w-1.5 h-1.5 rounded-full bg-emerald-500/70" />*/}
                  <span className="text-sm text-white/40">99.9% Fill Rate</span>
                </div>
                <div className="flex items-center gap-2">
                  {/*<div className="w-1.5 h-1.5 rounded-full bg-emerald-500/70" />*/}
                  <span className="text-sm text-white/40">Non-Custodial</span>
                </div>
              </div>
            </div>
            {/* Background decorative element */}
            <div className="absolute -right-16 md:-right-10 lg:right-10 -bottom-16 w-72 h-72 opacity-[0.015] pointer-events-none">
              <svg viewBox="0 0 100 100" fill="none" stroke="currentColor" strokeWidth="0.4" className="w-full h-full text-white">
                <rect x="10" y="10" width="80" height="80" rx="4" />
                <line x1="10" y1="30" x2="90" y2="30" />
                <line x1="30" y1="10" x2="30" y2="30" />
                <path d="M35 55 L45 65 L65 45" strokeWidth="2" />
              </svg>
            </div>
          </WobbleCard>
        </div>
      </div>
    </section>
  );
}


function LuminousStreamPipeline() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"]
  });

  const circuitOpacity = useTransform(scrollYProgress, [0, 0.3], [0, 1]);


  const modules = [
    {
      id: "risk",
      label: "RISK_ENGINE",
      title: "The Filter",
      description: "Rejects toxic flow. If a Master Trader deviates from risk parameters, the signal is killed instantly.",
      icon: Shield,
      status: "ACTIVE",
      temp: "42Â°C",
      position: "top", // Triangle top
    },
    {
      id: "ledger",
      label: "ATOMIC_LEDGER",
      title: "The Ledger",
      description: "Double-entry immutability. Every satoshi is tracked on an internal SQL ledger before external execution.",
      icon: BarChart3,
      status: "SYNCED",
      temp: "38Â°C",
      position: "left", // Triangle bottom-left
    },
    {
      id: "sentinel",
      label: "SENTINEL_CORE",
      title: "The Shield",
      description: "Zero-Knowledge Access. We execute trades without ever holding withdrawal permissions.",
      icon: Eye,
      status: "WATCHING",
      temp: "35Â°C",
      position: "right", // Triangle bottom-right
    },
  ];

  return (
    <section className="py-32 bg-[#010101] relative overflow-hidden" ref={containerRef}>
      {/* Spotlight Effect */}
      <Spotlight
        className="-top-40 left-0 md:-top-20 md:left-60"
        fill="white"
      />

      {/* Grid Background Pattern */}
      <div
        className={cn(
          "pointer-events-none absolute inset-0 [background-size:40px_40px] select-none",
          "[background-image:linear-gradient(to_right,#111_1px,transparent_1px),linear-gradient(to_bottom,#111_1px,transparent_1px)]",
        )}
      />

      {/* Circuit Maze Background */}
      <div className="absolute inset-0">
        {/* SVG Circuit Pattern */}
        <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none">
          <defs>
            {/* Animated gradient for the circuit lines */}
            <linearGradient id="circuitGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#0ea5e9" stopOpacity="0">
                <animate attributeName="stopOpacity" values="0;0.5;0" dur="3s" repeatCount="indefinite" />
              </stop>
              <stop offset="50%" stopColor="#06b6d4" stopOpacity="0.4">
                <animate attributeName="stopOpacity" values="0.4;0.8;0.4" dur="3s" repeatCount="indefinite" />
              </stop>
              <stop offset="100%" stopColor="#0ea5e9" stopOpacity="0">
                <animate attributeName="stopOpacity" values="0;0.5;0" dur="3s" repeatCount="indefinite" />
              </stop>
            </linearGradient>

            {/* Glow filter */}
            <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="2" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Static circuit traces - maze pattern */}
          <motion.g style={{ opacity: circuitOpacity }}>
            {/* Horizontal lines */}
            <line x1="0%" y1="20%" x2="30%" y2="20%" stroke="rgba(6,182,212,0.1)" strokeWidth="1" />
            <line x1="40%" y1="20%" x2="70%" y2="20%" stroke="rgba(6,182,212,0.1)" strokeWidth="1" />
            <line x1="80%" y1="20%" x2="100%" y2="20%" stroke="rgba(6,182,212,0.1)" strokeWidth="1" />

            <line x1="0%" y1="40%" x2="20%" y2="40%" stroke="rgba(6,182,212,0.1)" strokeWidth="1" />
            <line x1="35%" y1="40%" x2="65%" y2="40%" stroke="rgba(6,182,212,0.1)" strokeWidth="1" />
            <line x1="80%" y1="40%" x2="100%" y2="40%" stroke="rgba(6,182,212,0.1)" strokeWidth="1" />

            <line x1="10%" y1="60%" x2="40%" y2="60%" stroke="rgba(6,182,212,0.1)" strokeWidth="1" />
            <line x1="55%" y1="60%" x2="90%" y2="60%" stroke="rgba(6,182,212,0.1)" strokeWidth="1" />

            <line x1="0%" y1="80%" x2="25%" y2="80%" stroke="rgba(6,182,212,0.1)" strokeWidth="1" />
            <line x1="45%" y1="80%" x2="55%" y2="80%" stroke="rgba(6,182,212,0.1)" strokeWidth="1" />
            <line x1="75%" y1="80%" x2="100%" y2="80%" stroke="rgba(6,182,212,0.1)" strokeWidth="1" />

            {/* Vertical lines */}
            <line x1="20%" y1="10%" x2="20%" y2="40%" stroke="rgba(6,182,212,0.1)" strokeWidth="1" />
            <line x1="20%" y1="60%" x2="20%" y2="90%" stroke="rgba(6,182,212,0.1)" strokeWidth="1" />

            <line x1="50%" y1="0%" x2="50%" y2="30%" stroke="rgba(6,182,212,0.1)" strokeWidth="1" />
            <line x1="50%" y1="50%" x2="50%" y2="70%" stroke="rgba(6,182,212,0.1)" strokeWidth="1" />
            <line x1="50%" y1="85%" x2="50%" y2="100%" stroke="rgba(6,182,212,0.1)" strokeWidth="1" />

            <line x1="80%" y1="15%" x2="80%" y2="45%" stroke="rgba(6,182,212,0.1)" strokeWidth="1" />
            <line x1="80%" y1="55%" x2="80%" y2="85%" stroke="rgba(6,182,212,0.1)" strokeWidth="1" />

            {/* Corner connections */}
            <polyline points="30%,20% 35%,20% 35%,40%" fill="none" stroke="rgba(6,182,212,0.1)" strokeWidth="1" />
            <polyline points="65%,40% 65%,60% 55%,60%" fill="none" stroke="rgba(6,182,212,0.1)" strokeWidth="1" />
            <polyline points="25%,80% 25%,60% 10%,60%" fill="none" stroke="rgba(6,182,212,0.1)" strokeWidth="1" />
            <polyline points="75%,80% 80%,80% 80%,55%" fill="none" stroke="rgba(6,182,212,0.1)" strokeWidth="1" />

            {/* Animated pulse lines */}
            <path d="M 0,200 L 200,200 L 200,400 L 400,400 L 400,300" fill="none" stroke="url(#circuitGradient)" strokeWidth="2" filter="url(#glow)" />
            <path d="M 600,100 L 600,300 L 400,300 L 400,500" fill="none" stroke="url(#circuitGradient)" strokeWidth="2" filter="url(#glow)" style={{ animationDelay: '1s' }} />
          </motion.g>
        </svg>

        {/* Terminal-style system labels */}
        <motion.div className="absolute inset-0 pointer-events-none font-mono text-[9px] text-cyan-500/20" style={{ opacity: circuitOpacity }}>
          <span className="absolute top-[15%] left-[5%]">SYS_READY</span>
          <span className="absolute top-[25%] right-[8%]">CORE_TEMP: 38Â°C</span>
          <span className="absolute top-[45%] left-[12%]">BUFFER_OK</span>
          <span className="absolute top-[55%] right-[15%]">LATENCY: 12ms</span>
          <span className="absolute top-[75%] left-[8%]">MEM_ALLOC: 2.4GB</span>
          <span className="absolute top-[85%] right-[10%]">THREADS: 128</span>
          <span className="absolute top-[35%] left-[45%]">NEURAL_SYNC</span>
          <span className="absolute top-[65%] left-[55%]">LEDGER_HASH</span>
        </motion.div>
      </div>

      <div className="max-w-6xl mx-auto px-6 relative z-10">
        {/* Header */}
        <div className="text-center mb-20">

          <motion.h2
            className="text-4xl lg:text-6xl font-semibold tracking-tight text-white mb-6"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
          >
            Chase the moon. Weâ€™ll guard the rocket.
          </motion.h2>
          <motion.p
            className="text-lg text-white/40 max-w-2xl mx-auto"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
          >
            Crypto is wild but with our triple-layer security, your only job is growing your portfolio. Weâ€™ve got the rest covered.
          </motion.p>
        </div>

        {/* Glass Modules - Triangle Formation */}
        <div className="relative min-h-auto lg:min-h-[600px] flex flex-col lg:block items-center justify-center gap-12 mt-10 lg:mt-0">
          {/* Center connection point */}
          <div className="absolute w-4 h-4 rounded-full bg-cyan-500/30 blur-sm" />
          <div className="absolute w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />

          {/* Module Cards - Machined Hardware Chips */}
          {modules.map((module, i) => (
            <motion.div
              key={module.id}
              className={`relative lg:absolute ${module.position === 'top' ? 'lg:top-0 lg:left-1/2 lg:-translate-x-1/2' :
                module.position === 'left' ? 'lg:bottom-0 lg:left-[10%]' :
                  'lg:bottom-0 lg:right-[10%]'
                }`}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.15, duration: 0.5 }}
            >
              {/* Machined Chip with Chamfered Corners */}
              <div className="group relative w-[280px]">
                {/* Piano Black Body with 45-degree Chamfers */}
                <div
                  className="relative overflow-hidden"
                  style={{
                    clipPath: 'polygon(12px 0, calc(100% - 12px) 0, 100% 12px, 100% calc(100% - 12px), calc(100% - 12px) 100%, 12px 100%, 0 calc(100% - 12px), 0 12px)',
                    background: 'linear-gradient(180deg, #0a0a0a 0%, #050505 100%)',
                    boxShadow: '0 25px 50px -12px rgba(0,0,0,0.9)'
                  }}
                >
                  {/* Top Bevel Edge (1px highlight) */}
                  <div className="absolute top-0 left-3 right-3 h-px bg-gradient-to-r from-transparent via-white/[0.15] to-transparent" />

                  {/* Carbon Fiber Noise Texture Overlay */}
                  <div className="absolute inset-0 opacity-[0.03]" style={{
                    backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
                  }} />

                  <div className="relative p-5 pt-4">
                    {/* Top-Left Serial Label */}
                    <div className="mb-3">
                      <span className="font-mono text-[8px] text-white/15 uppercase tracking-[0.2em]">{module.label}</span>
                    </div>

                    {/* Schematic Viewport */}
                    <div className="relative w-full h-24 mb-4 border border-white/[0.04] bg-black/30 overflow-hidden">
                      {/* Razor-Sharp Schematics */}
                      {module.id === 'risk' && (
                        /* Shield Grid Wireframe */
                        <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 100">
                          <defs>
                            <linearGradient id="shieldGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                              <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.6" />
                              <stop offset="100%" stopColor="#dc2626" stopOpacity="0.2" />
                            </linearGradient>
                          </defs>
                          {/* Shield outline */}
                          <path d="M50 8 L85 25 L85 55 Q85 75 50 92 Q15 75 15 55 L15 25 Z"
                            fill="none" stroke="url(#shieldGrad)" strokeWidth="0.5" />
                          {/* Grid lines */}
                          {[30, 45, 60, 75].map((y, k) => (
                            <line key={k} x1="20" y1={y} x2="80" y2={y} stroke="#f59e0b" strokeOpacity="0.2" strokeWidth="0.3" />
                          ))}
                          {[35, 50, 65].map((x, k) => (
                            <line key={k} x1={x} y1="25" x2={x} y2="85" stroke="#f59e0b" strokeOpacity="0.2" strokeWidth="0.3" />
                          ))}
                          {/* Pulse animation */}
                          <circle cx="50" cy="50" r="8" fill="none" stroke="#f59e0b" strokeWidth="0.5" opacity="0.6">
                            <animate attributeName="r" values="8;20;8" dur="2s" repeatCount="indefinite" />
                            <animate attributeName="opacity" values="0.6;0;0.6" dur="2s" repeatCount="indefinite" />
                          </circle>
                        </svg>
                      )}

                      {module.id === 'ledger' && (
                        /* Hex Code Waterfall */
                        <div className="absolute inset-0 overflow-hidden font-mono text-[6px] text-cyan-500/40 leading-tight p-1">
                          <div className="animate-marquee-vertical">
                            {['0x8f3a', '0x2c91', '0xd4e7', '0x1b5f', '0xa920', '0x7c84', '0x3e6b', '0xf1a2', '0x5d79', '0x9c03', '0x4b8e', '0xe6f5'].map((hex, k) => (
                              <div key={k} className="whitespace-nowrap opacity-60">{hex} {hex} {hex} {hex}</div>
                            ))}
                          </div>
                          {/* Lock overlay */}
                          <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 100">
                            <rect x="35" y="40" width="30" height="25" fill="none" stroke="#06b6d4" strokeWidth="0.5" opacity="0.5" />
                            <path d="M43 40 L43 32 Q43 25 50 25 Q57 25 57 32 L57 40" fill="none" stroke="#06b6d4" strokeWidth="0.5" opacity="0.5" />
                          </svg>
                        </div>
                      )}

                      {module.id === 'sentinel' && (
                        /* Radar Sweep with Grid */
                        <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 100">
                          {/* Grid coordinates */}
                          <text x="5" y="15" fontSize="4" fill="#10b981" opacity="0.3">N</text>
                          <text x="90" y="55" fontSize="4" fill="#10b981" opacity="0.3">E</text>
                          <text x="47" y="98" fontSize="4" fill="#10b981" opacity="0.3">S</text>
                          <text x="2" y="55" fontSize="4" fill="#10b981" opacity="0.3">W</text>
                          {/* Concentric circles */}
                          {[15, 25, 35].map((r, k) => (
                            <circle key={k} cx="50" cy="50" r={r} fill="none" stroke="#10b981" strokeWidth="0.3" opacity="0.3" />
                          ))}
                          {/* Cross hairs */}
                          <line x1="50" y1="10" x2="50" y2="90" stroke="#10b981" strokeWidth="0.3" opacity="0.2" />
                          <line x1="10" y1="50" x2="90" y2="50" stroke="#10b981" strokeWidth="0.3" opacity="0.2" />
                          {/* Sweep */}
                          <line x1="50" y1="50" x2="50" y2="15" stroke="#10b981" strokeWidth="0.8" opacity="0.8">
                            <animateTransform attributeName="transform" type="rotate" from="0 50 50" to="360 50 50" dur="4s" repeatCount="indefinite" />
                          </line>
                          {/* Sweep trail */}
                          <path d="M50 50 L50 15 A35 35 0 0 1 85 50 Z" fill="url(#sweepGrad)" opacity="0.15">
                            <animateTransform attributeName="transform" type="rotate" from="0 50 50" to="360 50 50" dur="4s" repeatCount="indefinite" />
                          </path>
                          <defs>
                            <linearGradient id="sweepGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                              <stop offset="0%" stopColor="#10b981" />
                              <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
                            </linearGradient>
                          </defs>
                        </svg>
                      )}

                      {/* Corner markers */}
                      <div className="absolute top-1 left-1 w-2 h-2 border-l border-t border-white/10" />
                      <div className="absolute top-1 right-1 w-2 h-2 border-r border-t border-white/10" />
                      <div className="absolute bottom-1 left-1 w-2 h-2 border-l border-b border-white/10" />
                      <div className="absolute bottom-1 right-1 w-2 h-2 border-r border-b border-white/10" />
                    </div>

                    {/* Title - Laser Etched */}
                    <h3 className="font-mono text-[10px] font-medium text-white/50 uppercase tracking-[0.15em] mb-2">{module.title}</h3>

                    {/* Description - Dark Grey Etched */}
                    <p className="font-mono text-[9px] text-white/20 leading-relaxed mb-3">
                      {module.description}
                    </p>

                    {/* Status Bar */}
                    <div className="flex items-center gap-2 pt-2 border-t border-white/[0.03]">
                      <div className={`w-1 h-1 ${module.status === 'ACTIVE' ? 'bg-emerald-400' :
                        module.status === 'SYNCED' ? 'bg-cyan-400' :
                          'bg-amber-400'
                        }`} />
                      <span className="font-mono text-[7px] text-white/25 uppercase">{module.status}</span>
                      <span className="font-mono text-[7px] text-white/10">|</span>
                      <span className="font-mono text-[7px] text-white/15">{module.temp}</span>
                    </div>
                  </div>
                </div>

                {/* Cast Shadow */}
                <div className="absolute -bottom-3 left-2 right-2 h-3 bg-black/50 blur-lg" />
              </div>
            </motion.div>
          ))}

          {/* Connection Lines to Center */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: -1 }}>
            <defs>
              <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#06b6d4" stopOpacity="0" />
                <stop offset="50%" stopColor="#06b6d4" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#06b6d4" stopOpacity="0" />
              </linearGradient>
            </defs>
            {/* Lines from center to modules */}
            <motion.line x1="50%" y1="50%" x2="50%" y2="15%" stroke="url(#lineGradient)" strokeWidth="1" style={{ opacity: circuitOpacity }} />
            <motion.line x1="50%" y1="50%" x2="20%" y2="85%" stroke="url(#lineGradient)" strokeWidth="1" style={{ opacity: circuitOpacity }} />
            <motion.line x1="50%" y1="50%" x2="80%" y2="85%" stroke="url(#lineGradient)" strokeWidth="1" style={{ opacity: circuitOpacity }} />
          </svg>
        </div>

        {/* System Status Bar */}
        <motion.div
          className="mt-16 flex flex-wrap justify-center gap-8"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
        </motion.div>
      </div>
    </section>
  );
}

function Sparkline({ data, color = "#10b981" }: { data: number[]; color?: string }) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const width = 80;
  const height = 32;

  const points = data.map((value, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((value - min) / range) * height;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg width={width} height={height} className="overflow-visible">
      <defs>
        <linearGradient id={`gradient-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polyline
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
      <polygon
        fill={`url(#gradient-${color.replace('#', '')})`}
        points={`0,${height} ${points} ${width},${height}`}
      />
    </svg>
  );
}

function TradersSection() {
  const traders = [
    {
      rank: 1,
      name: "AlphaTrader",
      location: "Lagos, Nigeria",
      verified: true,
      roi: "+127.4%",
      winRate: 68,
      pnl: "+â‚¦847M",
      drawdown: "-12.3%",
      sharpe: 2.34,
      copiers: 847,
      aum: "â‚¦4.2B",
      style: "Trend Following",
      sparkData: [20, 35, 28, 45, 40, 55, 70, 65, 80, 75, 95, 127],
    },
    {
      rank: 2,
      name: "CryptoSage",
      location: "Nairobi, Kenya",
      verified: true,
      roi: "+89.2%",
      winRate: 72,
      pnl: "+â‚¦623M",
      drawdown: "-8.7%",
      sharpe: 1.98,
      copiers: 623,
      aum: "â‚¦2.8B",
      style: "Mean Reversion",
      sparkData: [15, 22, 30, 28, 42, 48, 55, 52, 68, 72, 80, 89],
    },
    {
      rank: 3,
      name: "WhaleWatcher",
      location: "Cape Town, SA",
      verified: true,
      roi: "+64.8%",
      winRate: 65,
      pnl: "+â‚¦412M",
      drawdown: "-18.5%",
      sharpe: 1.45,
      copiers: 412,
      aum: "â‚¦1.9B",
      style: "On-chain Analytics",
      sparkData: [10, 18, 15, 32, 28, 45, 42, 55, 50, 58, 62, 65],
    },
    {
      rank: 4,
      name: "QuantMaster",
      location: "Accra, Ghana",
      verified: true,
      roi: "+52.1%",
      winRate: 71,
      pnl: "+â‚¦298M",
      drawdown: "-9.2%",
      sharpe: 1.89,
      copiers: 298,
      aum: "â‚¦1.2B",
      style: "Statistical Arbitrage",
      sparkData: [12, 18, 22, 28, 32, 36, 38, 42, 44, 48, 50, 52],
    },
  ];

  const globeConfig = {
    pointSize: 4,
    globeColor: "#1a1a2e",
    showAtmosphere: true,
    atmosphereColor: "#10b981",
    atmosphereAltitude: 0.15,
    emissive: "#0f172a",
    emissiveIntensity: 0.3,
    shininess: 0.9,
    polygonColor: "rgba(16,185,129,0.4)",
    ambientLight: "#10b981",
    directionalLeftLight: "#ffffff",
    directionalTopLight: "#10b981",
    pointLight: "#ffffff",
    arcTime: 2000,
    arcLength: 0.9,
    rings: 1,
    maxRings: 3,
    initialPosition: { lat: 9.0820, lng: 8.6753 },
    autoRotate: true,
    autoRotateSpeed: 0.5,
  };

  // Emerald, Cyan, and Teal arcs
  const arcColors = ["#10b981", "#06b6d4", "#14b8a6", "#22c55e", "#0ea5e9"];

  const tradeArcs = [
    // Lagos to global hubs
    { order: 1, startLat: 6.5244, startLng: 3.3792, endLat: 1.3521, endLng: 103.8198, arcAlt: 0.4, color: arcColors[0] }, // Singapore
    { order: 1, startLat: 6.5244, startLng: 3.3792, endLat: 40.7128, endLng: -74.006, arcAlt: 0.5, color: arcColors[1] }, // NYC
    { order: 2, startLat: 6.5244, startLng: 3.3792, endLat: 51.5072, endLng: -0.1276, arcAlt: 0.3, color: arcColors[2] }, // London
    { order: 2, startLat: 6.5244, startLng: 3.3792, endLat: 35.6762, endLng: 139.6503, arcAlt: 0.5, color: arcColors[3] }, // Tokyo
    { order: 3, startLat: 6.5244, startLng: 3.3792, endLat: 22.3193, endLng: 114.1694, arcAlt: 0.4, color: arcColors[4] }, // Hong Kong
    { order: 3, startLat: 6.5244, startLng: 3.3792, endLat: 25.2048, endLng: 55.2708, arcAlt: 0.3, color: arcColors[0] }, // Dubai
    { order: 4, startLat: 6.5244, startLng: 3.3792, endLat: 48.8566, endLng: 2.3522, arcAlt: 0.25, color: arcColors[1] }, // Paris
    { order: 4, startLat: 6.5244, startLng: 3.3792, endLat: 37.7749, endLng: -122.4194, arcAlt: 0.6, color: arcColors[2] }, // SF

    // Nairobi connections
    { order: 2, startLat: -1.2921, startLng: 36.8219, endLat: 22.3193, endLng: 114.1694, arcAlt: 0.4, color: arcColors[0] }, // HK
    { order: 3, startLat: -1.2921, startLng: 36.8219, endLat: 35.6762, endLng: 139.6503, arcAlt: 0.5, color: arcColors[1] }, // Tokyo
    { order: 3, startLat: -1.2921, startLng: 36.8219, endLat: 19.076, endLng: 72.8777, arcAlt: 0.35, color: arcColors[2] }, // Mumbai
    { order: 4, startLat: -1.2921, startLng: 36.8219, endLat: 31.2304, endLng: 121.4737, arcAlt: 0.45, color: arcColors[3] }, // Shanghai
    { order: 5, startLat: -1.2921, startLng: 36.8219, endLat: 1.3521, endLng: 103.8198, arcAlt: 0.35, color: arcColors[4] }, // Singapore

    // Cape Town connections
    { order: 3, startLat: -33.9249, startLng: 18.4241, endLat: -33.8688, endLng: 151.2093, arcAlt: 0.5, color: arcColors[0] }, // Sydney
    { order: 4, startLat: -33.9249, startLng: 18.4241, endLat: 52.52, endLng: 13.405, arcAlt: 0.4, color: arcColors[1] }, // Berlin
    { order: 5, startLat: -33.9249, startLng: 18.4241, endLat: -23.5505, endLng: -46.6333, arcAlt: 0.5, color: arcColors[2] }, // Sao Paulo
    { order: 5, startLat: -33.9249, startLng: 18.4241, endLat: 51.5072, endLng: -0.1276, arcAlt: 0.4, color: arcColors[3] }, // London

    // Accra connections
    { order: 4, startLat: 5.6037, startLng: -0.187, endLat: 40.7128, endLng: -74.006, arcAlt: 0.4, color: arcColors[0] }, // NYC
    { order: 5, startLat: 5.6037, startLng: -0.187, endLat: 51.5072, endLng: -0.1276, arcAlt: 0.2, color: arcColors[1] }, // London
    { order: 6, startLat: 5.6037, startLng: -0.187, endLat: 48.8566, endLng: 2.3522, arcAlt: 0.22, color: arcColors[2] }, // Paris

    // Cross-Africa routes  
    { order: 5, startLat: 6.5244, startLng: 3.3792, endLat: -1.2921, endLng: 36.8219, arcAlt: 0.12, color: arcColors[3] }, // Lagos-Nairobi
    { order: 6, startLat: -1.2921, startLng: 36.8219, endLat: -33.9249, endLng: 18.4241, arcAlt: 0.15, color: arcColors[4] }, // Nairobi-Cape Town
    { order: 6, startLat: 6.5244, startLng: 3.3792, endLat: 5.6037, endLng: -0.187, arcAlt: 0.08, color: arcColors[0] }, // Lagos-Accra
    { order: 7, startLat: 6.5244, startLng: 3.3792, endLat: -33.9249, endLng: 18.4241, arcAlt: 0.2, color: arcColors[1] }, // Lagos-Cape Town
    { order: 7, startLat: 5.6037, startLng: -0.187, endLat: -1.2921, endLng: 36.8219, arcAlt: 0.15, color: arcColors[2] }, // Accra-Nairobi

    // Cairo connections
    { order: 6, startLat: 30.0444, startLng: 31.2357, endLat: 51.5072, endLng: -0.1276, arcAlt: 0.3, color: arcColors[3] }, // Cairo-London
    { order: 7, startLat: 30.0444, startLng: 31.2357, endLat: 25.2048, endLng: 55.2708, arcAlt: 0.15, color: arcColors[4] }, // Cairo-Dubai
    { order: 8, startLat: 30.0444, startLng: 31.2357, endLat: 6.5244, endLng: 3.3792, arcAlt: 0.18, color: arcColors[0] }, // Cairo-Lagos

    // Johannesburg connections
    { order: 7, startLat: -26.2041, startLng: 28.0473, endLat: 40.7128, endLng: -74.006, arcAlt: 0.55, color: arcColors[1] }, // Jo'burg-NYC
    { order: 8, startLat: -26.2041, startLng: 28.0473, endLat: 1.3521, endLng: 103.8198, arcAlt: 0.4, color: arcColors[2] }, // Jo'burg-Singapore
    { order: 8, startLat: -26.2041, startLng: 28.0473, endLat: -33.9249, endLng: 18.4241, arcAlt: 0.08, color: arcColors[3] }, // Jo'burg-Cape Town
  ];

  return (
    <section id="traders" className="py-24 bg-black relative overflow-hidden">
      {/* TextHoverEffect Headline */}
      <div className="h-[20rem] flex items-center justify-center">
        <TextHoverEffect text="AFRICA" duration={0.2} />
      </div>

      {/* Section Content */}
      <div className="max-w-7xl mx-auto px-6 text-center -mt-8">
        <motion.p
          className="text-lg md:text-xl text-white/50 max-w-2xl mx-auto leading-relaxed"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          Connecting <span className="text-emerald-400 font-medium">African</span> capital
          to global alpha. The infrastructure for the next generation of sovereign wealth.
        </motion.p>
      </div>

      {/* World Map Visualization */}
      <motion.div
        className="max-w-6xl mx-auto px-6 mt-12"
        initial={{ opacity: 0, scale: 0.95 }}
        whileInView={{ opacity: 1, scale: 1 }}
        viewport={{ once: true }}
        transition={{ delay: 0.3, duration: 0.8 }}
      >
        <div className="dark bg-black rounded-lg overflow-hidden">
          <WorldMap
            dots={[
              // Lagos to London
              { start: { lat: 6.5244, lng: 3.3792 }, end: { lat: 51.5074, lng: -0.1278 } },
              // Lagos to New York
              { start: { lat: 6.5244, lng: 3.3792 }, end: { lat: 40.7128, lng: -74.006 } },
              // Nairobi to Singapore
              { start: { lat: -1.2921, lng: 36.8219 }, end: { lat: 1.3521, lng: 103.8198 } },
              // Cape Town to Dubai
              { start: { lat: -33.9249, lng: 18.4241 }, end: { lat: 25.2048, lng: 55.2708 } },
              // Johannesburg to Hong Kong
              { start: { lat: -26.2041, lng: 28.0473 }, end: { lat: 22.3193, lng: 114.1694 } },
              // Accra to London
              { start: { lat: 5.6037, lng: -0.187 }, end: { lat: 51.5074, lng: -0.1278 } },
            ]}
            lineColor="#10b981"
          />
        </div>

        {/* Caption */}
        <p className="text-center mt-4 text-[10px] text-white/20 uppercase font-mono tracking-wider">
          Live trade connections across African financial hubs
        </p>
      </motion.div>

      {/* Trader Cards - Infinite Scroll */}
      <div className="max-w-7xl mx-auto px-6 mt-16">
        <InfiniteMovingCards
          items={[
            {
              name: "AlphaTrader",
              strategy: "Trend Following",
              roi: "+127.4%",
              winRate: "68%",
              cryptos: ["BTC", "ETH", "SOL", "USDT"],
            },
            {
              name: "CryptoSage",
              strategy: "Mean Reversion",
              roi: "+89.2%",
              winRate: "72%",
              cryptos: ["ETH", "AVAX", "ADA", "BNB"],
            },
            {
              name: "WhaleWatcher",
              strategy: "On-chain Analytics",
              roi: "+64.8%",
              winRate: "65%",
              cryptos: ["BTC", "XRP", "DOGE", "ADA"],
            },
            {
              name: "QuantMaster",
              strategy: "Statistical Arbitrage",
              roi: "+52.1%",
              winRate: "71%",
              cryptos: ["SOL", "BNB", "ETH", "DOGE"],
            },
            {
              name: "DeFiKing",
              strategy: "Yield Optimization",
              roi: "+78.3%",
              winRate: "69%",
              cryptos: ["ETH", "BNB", "SOL", "AVAX"],
            },
            {
              name: "ScalpPro",
              strategy: "High-Frequency Scalping",
              roi: "+94.6%",
              winRate: "74%",
              cryptos: ["BTC", "ETH", "SOL", "XRP"],
            },
          ]}
          direction="left"
          speed="slow"
        />

        {/* View All CTA */}
        <motion.div
          className="mt-10 text-center"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.4 }}
        >
          <Link href="/register">
            <Button variant="ghost" className="text-white/50 hover:text-white mb-8">
              View all verified traders
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </Link>

          {/* Disclaimer under CTA */}
          <p className="text-[9px] text-white/10 uppercase tracking-widest font-mono max-w-lg mx-auto mb-12">
            Trading digital assets involves significant risk. Capital at risk.
          </p>
        </motion.div>

        <div className="mt-8 border-t border-white/5 pt-8 pb-4">
          <p className="text-[10px] text-white/20 text-center leading-relaxed max-w-5xl mx-auto uppercase tracking-wide font-mono">
            <strong>Risk Warning:</strong> Cryptocurrency trading involves substantial risk of loss and is not suitable for every investor. The valuation of cryptocurrencies and related products may fluctuate dramatically. Past performance is not indicative of future results. All trading strategies and signals are provided for informational purposes only. JARS does not guarantee any profit or protection against loss. By using this platform, you acknowledge the inherent risks associated with algorithmic and copy trading in the digital asset markets. Connectivity speeds and sync lag (&lt;1ms) allow for high-frequency execution but do not eliminate market risk.
          </p>
        </div>

        {/* Trust Badges */}
        <motion.div
          className="mt-12 flex flex-wrap justify-center gap-8"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.5 }}
        >
          {[
            { icon: Clock, label: "6+ months track record" },
            { icon: Shield, label: "KYC verified" },
            { icon: BarChart3, label: "Audited performance" },
          ].map((badge, i) => (
            <div key={i} className="flex items-center gap-2 text-white/30">
              <badge.icon className="w-4 h-4" />
              <span className="text-sm">{badge.label}</span>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}


function PricingSection() {
  return (
    <section id="pricing" className="py-32 bg-[#020202] relative">
      <div className="max-w-6xl mx-auto px-6">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <h2 className="text-4xl lg:text-5xl font-semibold tracking-tight text-white mb-4">
            Pricing
          </h2>
          <p className="text-lg text-white/40 max-w-xl mx-auto">
            Start for free, then pay only when you're ready to deploy real capital.
          </p>
        </motion.div>
        <div className="grid lg:grid-cols-3 gap-6 lg:gap-0 lg:divide-x lg:divide-white/10">
          <motion.div
            className="p-8 lg:p-10"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
          >
            <div className="mb-6">
              <h3 className="text-lg font-medium text-white mb-1">Free</h3>
              <div className="flex items-baseline gap-2 mb-3">
                <span className="text-4xl font-semibold text-white">$0</span>
                <span className="text-sm text-white/40">per month</span>
              </div>
              <p className="text-sm text-white/50 leading-relaxed">
                For individuals to learn copy trading and validate strategies.
              </p>
            </div>

            <Link href="/register" className="block mb-8">
              <Button
                variant="outline"
                className="w-full h-11 rounded-lg border-white/20 bg-transparent text-white hover:bg-white/5 font-medium"
              >
                Sign up
              </Button>
            </Link>
            <div className="mb-6">
              <div className="flex items-center gap-2 mb-4">
                <Zap className="w-4 h-4 text-white/40" />
                <span className="text-sm font-medium text-white/60">Platform</span>
              </div>
              <ul className="space-y-3">
                {[
                  "$10,000 virtual capital",
                  "1 strategy subscription",
                  "Live market data",
                  "Full platform access",
                ].map((feature, i) => (
                  <li key={i} className="flex items-start gap-3 text-sm text-white/70">
                    <Check className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </div>
          </motion.div>

          <motion.div
            className="p-8 lg:p-10 bg-white/[0.02] lg:bg-transparent"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
          >
            <div className="mb-6">
              <h3 className="text-lg font-medium text-white mb-1">Plus</h3>
              <div className="flex items-baseline gap-2 mb-3">
                <span className="text-4xl font-semibold text-white">$15</span>
                <span className="text-sm text-white/40">per month</span>
              </div>
              <p className="text-sm text-white/50 leading-relaxed">
                For traders ready to deploy real capital with verified strategies.
              </p>
            </div>

            <Link href="/register" className="block mb-8">
              <Button className="w-full h-11 rounded-lg bg-white text-black hover:bg-white/90 font-medium">
                Get started
              </Button>
            </Link>
            <div className="mb-6">
              <p className="text-xs text-white/40 uppercase tracking-wider mb-4">Everything in Free</p>
              <ul className="space-y-3">
                {[
                  "Live capital deployment",
                  "Up to 3 strategy subscriptions",
                  "$1,000 allocation limit",
                  "Basic analytics",
                  "Email support",
                ].map((feature, i) => (
                  <li key={i} className="flex items-start gap-3 text-sm text-white/70">
                    <Check className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="pt-4 border-t border-white/10">
              <p className="text-xs text-white/40">+ 20% success fee on profits</p>
            </div>
          </motion.div>

          <motion.div
            className="p-8 lg:p-10"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.3 }}
          >
            <div className="mb-6">
              <h3 className="text-lg font-medium text-white mb-1">Business</h3>
              <div className="flex items-baseline gap-2 mb-3">
                <span className="text-4xl font-semibold text-white">$45</span>
                <span className="text-sm text-white/40">per month</span>
              </div>
              <p className="text-sm text-white/50 leading-relaxed">
                For professionals requiring advanced features and higher limits.
              </p>
            </div>

            <Link href="/register" className="block mb-8">
              <Button
                variant="outline"
                className="w-full h-11 rounded-lg border-white/20 bg-transparent text-white hover:bg-white/5 font-medium"
              >
                Get started
              </Button>
            </Link>

            <div className="mb-6">
              <p className="text-xs text-white/40 uppercase tracking-wider mb-4">Everything in Plus</p>
              <ul className="space-y-3">
                {[
                  "Unlimited capital & strategies",
                  "Priority execution (<30ms)",
                  "Advanced analytics suite",
                  "API access",
                  "Dedicated support channel",
                ].map((feature, i) => (
                  <li key={i} className="flex items-start gap-3 text-sm text-white/70">
                    <Check className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="pt-4 border-t border-white/10">
              <p className="text-xs text-white/40">+ 10% success fee on profits</p>
            </div>
          </motion.div>
        </div>
        <motion.div
          className="mt-16 pt-12 border-t border-white/10 text-center"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.4 }}
        >
          <p className="text-white/50 mb-3">
            Need higher limits or custom infrastructure?
          </p>
          <a
            href="mailto:enterprise@jars.io"
            className="inline-flex items-center gap-2 text-white hover:text-white/80 transition-colors font-medium"
          >
            Contact Sales
            <ArrowRight className="w-4 h-4" />
          </a>
        </motion.div>
      </div>
    </section>
  );
}



function FAQSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const faqs = [
    { q: "Is my money safe with JARS?", a: "JARS is 100% non-custodial, we never hold your funds. Your assets remain on your exchange (Binance/Bybit) at all times. We only use API keys with trade permissions, never withdrawal access." },
    { q: "What exchanges do you support?", a: "Currently we support Bybit for both Spot and Futures trading. OKX, KuCoin, Binance, and Bitget integrations are coming soon." },
    { q: "How fast is the execution?", a: "Our sentinel engine achieves average latencies under 50ms from signal detection to order fill. This is faster than most manual traders can even react." },
    { q: "Can I stop copying at any time?", a: "Absolutely. You have full control. Pause or stop copying instantly through your dashboard, or use the Kill Switch to revoke all API access immediately." },
    { q: "What is the minimum to start?", a: "You can start with as little as $10" },
    { q: "How are traders verified?", a: "All traders undergo a 6-month audit period. We verify their identity (KYC), audit their trading history, enforce max drawdown limits, and monitor ongoing performance." },
  ];

  return (
    <section id="faq" className="py-24 bg-[#020202] relative">
      <div className="max-w-3xl mx-auto px-6 relative z-10">

        {/* Section Header */}
        <div className="text-center mb-16">
          <motion.p
            className="text-white/40 text-sm font-medium mb-4"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            Have questions?
          </motion.p>
          <motion.h2
            className="text-4xl lg:text-5xl font-semibold tracking-tight text-white mb-4"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
          >
            Frequently asked
          </motion.h2>
          <motion.p
            className="text-lg text-white/50"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
          >
            Everything you need to know about the platform.
          </motion.p>
        </div>
        <div className="space-y-2">
          {faqs.map((faq, i) => (
            <motion.div
              key={i}
              className="rounded-xl bg-white/[0.02] border border-white/5 overflow-hidden hover:border-white/10 transition-colors"
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.05 }}
            >
              <button
                onClick={() => setOpenIndex(openIndex === i ? null : i)}
                className="w-full px-6 py-5 flex items-center justify-between text-left"
              >
                <span className="text-base font-medium text-white pr-4">{faq.q}</span>
                <motion.div
                  animate={{ rotate: openIndex === i ? 180 : 0 }}
                  transition={{ duration: 0.2 }}
                  className="flex-shrink-0"
                >
                  <ChevronDown className="w-5 h-5 text-white/40" />
                </motion.div>
              </button>
              <AnimatePresence>
                {openIndex === i && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden"
                  >
                    <div className="px-6 pb-5">
                      <p className="text-[15px] text-white/50 leading-relaxed">{faq.a}</p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>
        <motion.div
          className="mt-12 text-center"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.3 }}
        >
          <p className="text-white/40 text-sm mb-4">Still have questions?</p>
          <a href="#" className="text-emerald-400 text-sm font-medium hover:text-emerald-300 transition-colors">
            Contact our support team â†’
          </a>
        </motion.div>
      </div>
    </section>
  );
}


export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#020202] text-white antialiased">
      {/* Film Grain Noise Overlay */}
      <div className="bg-noise" />

      {/* Navigation - Glassmorphism */}
      <nav className="fixed top-4 left-1/2 -translate-x-1/2 z-50 w-[calc(100%-2rem)] max-w-5xl">
        <div className="relative rounded-2xl bg-white/[0.03] backdrop-blur-2xl border border-white/[0.08] shadow-[0_8px_32px_rgba(0,0,0,0.4)]">
          {/* Inner glow effect */}
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-white/[0.05] to-transparent pointer-events-none" />

          <div className="relative px-6 h-14 flex items-center justify-between">
            <Link href="/" className="text-xl font-semibold tracking-tight text-white">
              jars_
            </Link>

            <div className="hidden lg:flex items-center gap-8">
              {[
                { href: "#infrastructure", label: "Infrastructure" },
                { href: "#traders", label: "Traders" },
                { href: "#pricing", label: "Pricing" },
                { href: "#faq", label: "FAQ" },
              ].map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  className="text-sm text-white/50 hover:text-white transition-colors font-medium"
                >
                  {link.label}
                </a>
              ))}
            </div>

            <div className="flex items-center gap-4">
              <div className="hidden lg:flex items-center gap-4 mr-4 border-r border-white/10 pr-6">
                <a
                  href="https://github.com/astrovine/jars"
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-2 text-sm font-medium text-white/50 hover:text-white transition-colors"
                >
                  <Github className="w-4 h-4" />
                  <span className="hidden xl:inline">Star on GitHub</span>
                </a>
              </div>

              <Link href="/register">
                <Button className="bg-white text-black hover:bg-white/90 rounded-full h-9 px-5 text-sm font-semibold shadow-lg">
                  Create Account
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <section className="relative pt-36 pb-8 lg:pt-48 lg:pb-16 overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-emerald-900/10 via-transparent to-transparent" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[400px] bg-emerald-500/20 blur-[120px] rounded-full pointer-events-none" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[300px] bg-indigo-500/10 blur-[100px] rounded-full pointer-events-none" />


        <div className="max-w-[1600px] mx-auto px-6 relative z-10">
          <motion.h1
            className="text-[clamp(3.5rem,12vw,10rem)] font-semibold leading-[0.85] tracking-tighter mb-10"
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            Copy trades.<br />
            <span className="text-white/10">
              <RotatingWords
                words={["Automatically.", "Instantly.", "Securely.", "Seamlessly."]}
                interval={5000}
              />
            </span>
          </motion.h1>

          <motion.p
            className="text-xl lg:text-2xl text-white/40 max-w-2xl leading-relaxed mb-14"
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            Copy the wins, skip the stress. Mirror moves in{" "}
            <span className="text-white/70 font-medium">under 50 milliseconds</span>.
            {" "}We provide the speed, you keep the keys.
          </motion.p>

          <motion.div
            className="flex flex-col sm:flex-row items-center gap-6 mb-16"
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            {/* Professional CLI Install Box */}
            <div className="flex items-center gap-3 p-1.5 pl-4 pr-2 rounded-xl bg-[#1a1a1a] border border-white/10 shadow-xl shadow-black/50 group">
              <div className="flex items-center gap-3">
                <span className="text-emerald-500 font-mono select-none">$</span>
                <span className="font-mono text-white text-sm">pipx install jars-cli</span>
              </div>
              <div className="h-6 w-px bg-white/10 mx-1" />
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-white/40 hover:text-white hover:bg-white/10 rounded-lg"
                onClick={() => {
                  navigator.clipboard.writeText("pipx install jars-cli");
                }}
              >
                <Copy className="w-3.5 h-3.5" />
              </Button>
            </div>

            <span className="text-sm text-white/30 hidden sm:inline-block">or</span>

            <Link href="/register">
              <span className="text-sm font-medium text-white/40 hover:text-white transition-colors border-b border-transparent hover:border-white/40 pb-0.5">
                View documentation
              </span>
            </Link>
          </motion.div>

          {/* Stats */}
          <motion.div
            className="flex flex-wrap items-center gap-10 lg:gap-20 py-8 border-t border-white/5"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            <div>
              <div className="text-4xl lg:text-5xl font-semibold font-mono">50<span className="text-white/30">ms</span></div>
              <div className="text-xs text-white/30 uppercase tracking-wider mt-2">Latency Budget</div>
            </div>
            <div>
              <div className="text-4xl lg:text-5xl font-semibold font-mono">10k<span className="text-white/30">+</span></div>
              <div className="text-xs text-white/30 uppercase tracking-wider mt-2">Events/Sec</div>
            </div>
            <div>
              <div className="text-4xl lg:text-5xl font-semibold font-mono">256<span className="text-white/30">-bit</span></div>
              <div className="text-xs text-white/30 uppercase tracking-wider mt-2">Encryption</div>
            </div>
            <div>
              <div className="text-4xl lg:text-5xl font-semibold font-mono">24/7</div>
              <div className="text-xs text-white/30 uppercase tracking-wider mt-2">Sentinel Uptime</div>
            </div>
          </motion.div>

          {/* Disclaimer */}
          <p className="text-[10px] text-white/15 mt-8 max-w-xl">
            Crypto is volatile. Past performance is not indicative of future results. Non-custodial execution.
          </p>
        </div>
      </section>

      <CryptoMarquee />

      <section className="bg-[#020202] overflow-hidden">
        <ContainerScroll
          titleComponent={
            <div className="text-center mb-8">
              <h2 className="text-4xl md:text-6xl font-semibold tracking-tight text-white mb-4">
                Command Center
              </h2>
              <p className="text-lg text-white/40 max-w-xl mx-auto">
                Institutional-grade execution monitoring.{" "}
                <span className="text-white/60">Every millisecond. Every trade.</span>
              </p>
            </div>
          }
        >
          <TerminalDemo />
        </ContainerScroll>
      </section>

      <InfrastructureSection />
      <TradersSection />
      <LuminousStreamPipeline />
      <PricingSection />
      <FAQSection />

      <section className="py-32 bg-[#020202] relative">
        <div className="max-w-3xl mx-auto px-6 text-center relative z-10">
          <motion.h2
            className="text-4xl lg:text-5xl font-semibold tracking-tight text-white mb-6"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            Ready to automate your edge?
          </motion.h2>
          <motion.p
            className="text-lg text-white/50 mb-10 max-w-lg mx-auto"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
          >
            Join pro traders already copying the best. Start in under 5 minutes.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
          >
            <Link href="/register">
              <Button className="h-14 px-10 bg-white text-black hover:bg-white/90 rounded-xl text-base font-semibold">
                Open free account
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
          </motion.div>

          <motion.p
            className="text-sm text-white/30 mt-8"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.3 }}
          >
            No credit card required Â· Non-custodial
          </motion.p>
        </div>
      </section>

      <footer className="bg-[#0a0a0a] border-t border-white/5">
        {/* Top Links Bar */}
        <div className="border-b border-white/5 py-4">
          <div className="max-w-7xl mx-auto px-6 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-4 text-sm">
              <a href="#" className="text-white/60 hover:text-white transition-colors">Customer Relationship Summaries</a>
              <span className="text-white/20">|</span>
              <a href="#" className="text-white/60 hover:text-white transition-colors">Risk Disclosure</a>
            </div>
            <div className="flex items-center gap-2 text-sm text-white/40">
              <span>Follow us on</span>
              <div className="flex items-center gap-4 ml-2">
                <a href="#" className="text-white/60 hover:text-white transition-colors">ð•</a>
                <a href="#" className="text-white/60 hover:text-white transition-colors">Discord</a>
                <a href="#" className="text-white/60 hover:text-white transition-colors">Telegram</a>
                <a href="#" className="text-white/60 hover:text-white transition-colors">GitHub</a>
              </div>
            </div>
          </div>
        </div>

        {/* Main Footer Content */}
        <div className="max-w-7xl mx-auto px-6 py-16">
          <div className="grid lg:grid-cols-5 gap-12 mb-16">
            {/* Platform */}
            <div>
              <h4 className="text-sm font-semibold text-white mb-6">Platform</h4>
              <ul className="space-y-4">
                {["How it Works", "Copy Trading", "Traders", "Pricing", "Security"].map((item, i) => (
                  <li key={i}>
                    <a href="#" className="text-sm text-white/50 hover:text-white transition-colors">{item}</a>
                  </li>
                ))}
              </ul>
            </div>

            {/* Company */}
            <div>
              <h4 className="text-sm font-semibold text-white mb-6">Company</h4>
              <ul className="space-y-4">
                {["About Us", "Blog", "Careers", "Press", "Contact"].map((item, i) => (
                  <li key={i}>
                    <a href="#" className="text-sm text-white/50 hover:text-white transition-colors">{item}</a>
                  </li>
                ))}
              </ul>
            </div>

            {/* Legal & Regulatory */}
            <div>
              <h4 className="text-sm font-semibold text-white mb-6">Legal & Regulatory</h4>
              <ul className="space-y-4">
                {[
                  { label: "Terms of Service", href: "/terms" },
                  { label: "Privacy Policy", href: "/privacy" },
                  { label: "Risk Disclosure", href: "#" },
                  { label: "AML Policy", href: "#" },
                  { label: "Cookie Policy", href: "#" },
                ].map((item, i) => (
                  <li key={i}>
                    <Link href={item.href} className="text-sm text-white/50 hover:text-white transition-colors">{item.label}</Link>
                  </li>
                ))}
              </ul>
            </div>

            {/* Resources */}
            <div>
              <h4 className="text-sm font-semibold text-white mb-6">Resources</h4>
              <ul className="space-y-4">
                {["Documentation", "API Reference", "Status Page", "Changelog", "Support"].map((item, i) => (
                  <li key={i}>
                    <a href="#" className="text-sm text-white/50 hover:text-white transition-colors">{item}</a>
                  </li>
                ))}
              </ul>
            </div>

            {/* System Status */}
            <div>
              <h4 className="text-sm font-semibold text-white mb-6">System Status</h4>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-sm text-emerald-400">All Systems Operational</span>
              </div>
              <p className="text-xs text-white/30 leading-relaxed">
                Real-time infrastructure monitoring. 99.9% uptime target.
              </p>
            </div>
          </div>

          {/* Risk Disclosure */}
          <div className="border-t border-white/5 pt-12 mb-12">
            <h5 className="text-sm font-semibold text-white mb-4">All investing involves risk.</h5>
            <div className="space-y-4 text-xs text-white/40 leading-relaxed max-w-4xl">
              <p>
                <strong className="text-white/60">Copy trading services</strong> are provided by JARS Technologies Ltd. JARS operates as a technology provider and does not provide financial advice, investment recommendations, or act as a broker-dealer. Past performance of traders is not indicative of future results.
              </p>
              <p>
                <strong className="text-white/60">Cryptocurrency trading</strong> involves substantial risk of loss and is not suitable for all investors. The value of cryptocurrencies can be extremely volatile and you may lose more than your initial investment. You should carefully consider your investment objectives, level of experience, and risk appetite before using our services.
              </p>
              <p>
                <strong className="text-white/60">Non-custodial architecture</strong> means JARS never holds or has access to your funds. Your assets remain on your connected exchange at all times. You are responsible for the security of your exchange accounts and API keys.
              </p>
              <p>
                By using JARS, you acknowledge that you have read and understood our <Link href="/terms" className="text-white/60 underline hover:text-white">Terms of Service</Link>, <Link href="/privacy" className="text-white/60 underline hover:text-white">Privacy Policy</Link>, and Risk Disclosure. JARS is not available in all jurisdictions. Check local regulations before using our services.
              </p>
            </div>
          </div>

          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 text-xs text-white/30">
            <div>
              <p>Ivy Technologies Ltd. Â© 2026. All rights reserved.</p>
              <p className="mt-1">Lagos, Nigeria</p>
            </div>
            <div className="flex items-center gap-6">
              <a href="#" className="hover:text-white transition-colors">Your Privacy Choices</a>
              <a href="#" className="hover:text-white transition-colors">Accessibility</a>
              <a href="#" className="hover:text-white transition-colors">Sitemap</a>
            </div>
          </div>
        </div>
        <div className="bg-[#050505] py-16 overflow-hidden">
          <div className="max-w-7xl mx-auto px-6">
            <span className="block text-[clamp(4rem,20vw,16rem)] font-bold tracking-tighter text-white/[0.03] leading-none select-none">
              JARS
            </span>
          </div>
        </div>
      </footer>

      <CookieConsent />
    </div>
  );
}
