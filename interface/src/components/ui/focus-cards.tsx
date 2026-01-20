"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";

export const Card = React.memo(
    ({
        card,
        index,
        hovered,
        setHovered,
    }: {
        card: any;
        index: number;
        hovered: number | null;
        setHovered: React.Dispatch<React.SetStateAction<number | null>>;
    }) => (
        <div
            onMouseEnter={() => setHovered(index)}
            onMouseLeave={() => setHovered(null)}
            className={cn(
                "rounded-2xl relative bg-neutral-900 overflow-hidden h-[500px] w-full transition-all duration-300 ease-out border border-white/10",
                hovered !== null && hovered !== index && "blur-sm scale-[0.98] opacity-50",
                card.bgClass // Add custom background class support
            )}
        >
            {card.src && (
                <img
                    src={card.src}
                    alt={card.title}
                    className="object-cover absolute inset-0 w-full h-full opacity-50 transition-opacity duration-300"
                />
            )}
            {/* Dark overlay for readability (lighter if no image) */}
            <div className={cn("absolute inset-0", card.src ? "bg-black/60" : "bg-black/20")} />

            <div
                className={cn(
                    "absolute inset-0 flex flex-col justify-end p-8 transition-opacity duration-300",
                    // Always visible for pricing, but maybe highlight on hover?
                    // Keeping user's original logic: visible only on hover?
                    // For pricing, it must be visible. I'll modify logic to be always visible but "focused" style.
                    "opacity-100"
                )}
            >
                <div className="text-2xl md:text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-b from-neutral-50 to-neutral-200 mb-2">
                    {card.title}
                </div>
                {card.content && (
                    <div className="text-neutral-300 text-sm">{card.content}</div>
                )}
            </div>
        </div>
    )
);

Card.displayName = "Card";

type Card = {
    title: string;
    src?: string;
    bgClass?: string;
    content?: React.ReactNode;
};

export function FocusCards({ cards }: { cards: Card[] }) {
    const [hovered, setHovered] = useState<number | null>(null);

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-7xl mx-auto w-full">
            {cards.map((card, index) => (
                <Card
                    key={card.title}
                    card={card}
                    index={index}
                    hovered={hovered}
                    setHovered={setHovered}
                />
            ))}
        </div>
    );
}
