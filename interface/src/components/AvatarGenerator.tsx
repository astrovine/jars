"use client";

import React, { useMemo } from 'react';

const COLORS = [
    "#10B981", // Emerald
    "#3B82F6", // Blue
    "#6366F1", // Indigo
    "#8B5CF6", // Violet
    "#EC4899", // Pink
    "#F59E0B", // Amber
    "#06B6D4", // Cyan
];

const SHAPES = ['circle', 'rect', 'triangle'];

export function AvatarGenerator({ name, size = 64, className = "" }: { name: string; size?: number; className?: string }) {
    const seed = useMemo(() => {
        let hash = 0;
        for (let i = 0; i < name.length; i++) {
            hash = name.charCodeAt(i) + ((hash << 5) - hash);
        }
        return Math.abs(hash);
    }, [name]);

    // Deterministic random generator based on seed
    const getRandom = (offset: number) => {
        const x = Math.sin(seed + offset) * 10000;
        return x - Math.floor(x);
    };

    const getInt = (offset: number, min: number, max: number) => {
        return Math.floor(getRandom(offset) * (max - min + 1)) + min;
    };

    return (
        <div className={`overflow-hidden rounded-2xl bg-[#0A0A0A] ${className}`} style={{ width: size, height: size }}>
            <svg
                viewBox="0 0 100 100"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="w-full h-full"
            >
                {/* Abstract Background base */}
                <rect width="100" height="100" fill="#111" />

                {/* Generate 3 random geometric shapes */}
                <circle
                    cx={getInt(1, 20, 80)}
                    cy={getInt(2, 20, 80)}
                    r={getInt(3, 20, 40)}
                    fill={COLORS[seed % COLORS.length]}
                    opacity="0.2"
                />

                <rect
                    x={getInt(4, 10, 60)}
                    y={getInt(5, 10, 60)}
                    width={getInt(6, 30, 60)}
                    height={getInt(7, 30, 60)}
                    fill={COLORS[(seed + 1) % COLORS.length]}
                    opacity="0.3"
                    transform={`rotate(${getInt(8, 0, 90)} 50 50)`}
                />

                <path
                    d={`M${getInt(9, 10, 90)} ${getInt(10, 10, 90)} L${getInt(11, 10, 90)} ${getInt(12, 10, 90)} L${getInt(13, 10, 90)} ${getInt(14, 10, 90)} Z`}
                    fill={COLORS[(seed + 2) % COLORS.length]}
                    opacity="0.4"
                />

                {/* Overlay Grain for Texture */}
                <filter id="noiseFilter">
                    <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="3" stitchTiles="stitch" />
                </filter>
                <rect width="100%" height="100%" filter="url(#noiseFilter)" opacity="0.15" />
            </svg>
        </div>
    );
}
