"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface PointerHighlightProps {
    children: React.ReactNode;
    className?: string;
    highlightClassName?: string;
}

export function PointerHighlight({
    children,
    className,
    highlightClassName,
}: PointerHighlightProps) {
    const [isHovered, setIsHovered] = useState(false);
    const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
    const containerRef = useRef<HTMLSpanElement>(null);

    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (!containerRef.current) return;
            const rect = containerRef.current.getBoundingClientRect();
            setMousePosition({
                x: e.clientX - rect.left,
                y: e.clientY - rect.top,
            });
        };

        if (isHovered) {
            window.addEventListener("mousemove", handleMouseMove);
        }

        return () => {
            window.removeEventListener("mousemove", handleMouseMove);
        };
    }, [isHovered]);

    return (
        <motion.span
            ref={containerRef}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            className={cn(
                "relative inline-block cursor-pointer",
                className
            )}
        >
            {/* Highlight background */}
            <motion.span
                className={cn(
                    "absolute inset-0 rounded-md bg-emerald-500/20",
                    highlightClassName
                )}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{
                    opacity: isHovered ? 1 : 0,
                    scale: isHovered ? 1 : 0.8,
                }}
                transition={{ duration: 0.2 }}
            />

            {/* Pointer dot that follows mouse */}
            {isHovered && (
                <motion.span
                    className="absolute w-2 h-2 rounded-full bg-emerald-400 pointer-events-none z-10"
                    style={{
                        left: mousePosition.x - 4,
                        top: mousePosition.y - 4,
                    }}
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0 }}
                    transition={{ duration: 0.1 }}
                />
            )}

            {/* Text content */}
            <span className="relative z-[1]">{children}</span>
        </motion.span>
    );
}

export default PointerHighlight;
