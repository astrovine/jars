"use client";

import { cn } from "@/lib/utils";
import React, { useEffect, useState } from "react";

export const InfiniteMovingCards = ({
    items,
    direction = "left",
    speed = "fast",
    pauseOnHover = true,
    className,
}: {
    items: {
        name: string;
        strategy: string;
        roi: string;
        winRate: string;
        cryptos: string[];
    }[];
    direction?: "left" | "right";
    speed?: "fast" | "normal" | "slow";
    pauseOnHover?: boolean;
    className?: string;
}) => {
    const containerRef = React.useRef<HTMLDivElement>(null);
    const scrollerRef = React.useRef<HTMLUListElement>(null);

    useEffect(() => {
        addAnimation();
    }, []);

    const [start, setStart] = useState(false);

    function addAnimation() {
        if (containerRef.current && scrollerRef.current) {
            const scrollerContent = Array.from(scrollerRef.current.children);

            scrollerContent.forEach((item) => {
                const duplicatedItem = item.cloneNode(true);
                if (scrollerRef.current) {
                    scrollerRef.current.appendChild(duplicatedItem);
                }
            });

            getDirection();
            getSpeed();
            setStart(true);
        }
    }

    const getDirection = () => {
        if (containerRef.current) {
            if (direction === "left") {
                containerRef.current.style.setProperty(
                    "--animation-direction",
                    "forwards"
                );
            } else {
                containerRef.current.style.setProperty(
                    "--animation-direction",
                    "reverse"
                );
            }
        }
    };

    const getSpeed = () => {
        if (containerRef.current) {
            if (speed === "fast") {
                containerRef.current.style.setProperty("--animation-duration", "20s");
            } else if (speed === "normal") {
                containerRef.current.style.setProperty("--animation-duration", "40s");
            } else {
                containerRef.current.style.setProperty("--animation-duration", "80s");
            }
        }
    };

    // Crypto icons mapping
    const cryptoIcons: { [key: string]: string } = {
        BTC: "https://cryptologos.cc/logos/bitcoin-btc-logo.svg?v=035",
        ETH: "https://cryptologos.cc/logos/ethereum-eth-logo.svg?v=035",
        SOL: "https://cryptologos.cc/logos/solana-sol-logo.svg?v=035",
        BNB: "https://cryptologos.cc/logos/bnb-bnb-logo.svg?v=035",
        XRP: "https://cryptologos.cc/logos/xrp-xrp-logo.svg?v=035",
        DOGE: "https://cryptologos.cc/logos/dogecoin-doge-logo.svg?v=035",
        ADA: "https://cryptologos.cc/logos/cardano-ada-logo.svg?v=035",
        AVAX: "https://cryptologos.cc/logos/avalanche-avax-logo.svg?v=035",
    };

    return (
        <div
            ref={containerRef}
            className={cn(
                "scroller relative z-20 max-w-7xl overflow-hidden [mask-image:linear-gradient(to_right,transparent,white_20%,white_80%,transparent)]",
                className
            )}
        >
            <ul
                ref={scrollerRef}
                className={cn(
                    "flex min-w-full shrink-0 gap-4 py-4 w-max flex-nowrap",
                    start && "animate-scroll",
                    pauseOnHover && "hover:[animation-play-state:paused]"
                )}
            >
                {items.map((item, idx) => (
                    <li
                        className="w-[350px] max-w-full relative rounded-2xl border border-white/10 bg-gradient-to-b from-white/[0.05] to-transparent px-6 py-5 flex-shrink-0"
                        key={item.name + idx}
                    >
                        <div className="flex items-start justify-between mb-4">
                            <div>
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="text-white font-semibold">{item.name}</span>
                                    <span className="w-2 h-2 rounded-full bg-emerald-500" />
                                </div>
                                <span className="text-xs text-emerald-400">{item.strategy}</span>
                            </div>
                            <span className="text-emerald-400 font-bold text-lg">{item.roi}</span>
                        </div>

                        <div className="flex items-center justify-between mb-4">
                            <div className="flex -space-x-2">
                                {item.cryptos.slice(0, 4).map((crypto, i) => (
                                    <div
                                        key={i}
                                        className="w-7 h-7 rounded-full bg-white/10 border border-white/10 flex items-center justify-center overflow-hidden"
                                    >
                                        {cryptoIcons[crypto] ? (
                                            <img
                                                src={cryptoIcons[crypto]}
                                                alt={crypto}
                                                className="w-4 h-4"
                                            />
                                        ) : (
                                            <span className="text-[10px] text-white/60">{crypto}</span>
                                        )}
                                    </div>
                                ))}
                            </div>
                            <span className="text-xs text-white/40">{item.winRate} win rate</span>
                        </div>

                        <button className="w-full h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm font-medium hover:bg-emerald-500/20 transition-colors">
                            Copy Trader
                        </button>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default InfiniteMovingCards;
