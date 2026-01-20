"use client";

import { motion, useMotionTemplate, useMotionValue } from "framer-motion";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

interface RippleProps {
    x: number;
    y: number;
    size: number;
    key: number;
}

export function BackgroundRippleEffect({
    className,
    containerClassName,
}: {
    className?: string;
    containerClassName?: string;
}) {
    const containerRef = useRef<HTMLDivElement>(null);
    const [ripples, setRipples] = useState<RippleProps[]>([]);
    const rippleCountRef = useRef(0);

    const mouseX = useMotionValue(0);
    const mouseY = useMotionValue(0);

    const handleMouseMove = useCallback(
        (e: React.MouseEvent<HTMLDivElement>) => {
            if (!containerRef.current) return;
            const { left, top } = containerRef.current.getBoundingClientRect();
            mouseX.set(e.clientX - left);
            mouseY.set(e.clientY - top);
        },
        [mouseX, mouseY]
    );

    const handleClick = useCallback(
        (e: React.MouseEvent<HTMLDivElement>) => {
            if (!containerRef.current) return;
            const { left, top } = containerRef.current.getBoundingClientRect();
            const x = e.clientX - left;
            const y = e.clientY - top;
            const size = Math.max(
                containerRef.current.offsetWidth,
                containerRef.current.offsetHeight
            );

            const newRipple = {
                x,
                y,
                size: size * 2,
                key: rippleCountRef.current++,
            };

            setRipples((prev) => [...prev, newRipple]);

            setTimeout(() => {
                setRipples((prev) => prev.filter((r) => r.key !== newRipple.key));
            }, 1000);
        },
        []
    );

    useEffect(() => {
        const container = containerRef.current;
        if (!container) return;

        const resizeObserver = new ResizeObserver(() => {
            // Handle resize if needed
        });

        resizeObserver.observe(container);

        return () => {
            resizeObserver.disconnect();
        };
    }, []);

    return (
        <div
            ref={containerRef}
            onMouseMove={handleMouseMove}
            onClick={handleClick}
            className={cn(
                "absolute inset-0 overflow-hidden bg-transparent",
                containerClassName
            )}
        >
            {/* Grid Pattern */}
            <div
                className={cn(
                    "pointer-events-none absolute inset-0 [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black)]",
                    className
                )}
            >
                <div className="absolute inset-0 bg-grid-white/[0.02] bg-[length:50px_50px]" />
            </div>

            {/* Mouse Glow */}
            <motion.div
                className="pointer-events-none absolute -inset-px rounded-xl opacity-0 transition duration-300 group-hover:opacity-100"
                style={{
                    background: useMotionTemplate`
            radial-gradient(
              350px circle at ${mouseX}px ${mouseY}px,
              rgba(16, 185, 129, 0.1),
              transparent 80%
            )
          `,
                }}
            />

            {/* Ripple Effects */}
            {ripples.map((ripple) => (
                <motion.div
                    key={ripple.key}
                    className="absolute pointer-events-none rounded-full bg-emerald-500/10"
                    initial={{
                        x: ripple.x - 5,
                        y: ripple.y - 5,
                        width: 10,
                        height: 10,
                        opacity: 0.8,
                    }}
                    animate={{
                        x: ripple.x - ripple.size / 2,
                        y: ripple.y - ripple.size / 2,
                        width: ripple.size,
                        height: ripple.size,
                        opacity: 0,
                    }}
                    transition={{
                        duration: 1,
                        ease: "easeOut",
                    }}
                />
            ))}
        </div>
    );
}

export default BackgroundRippleEffect;
