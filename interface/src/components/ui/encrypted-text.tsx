"use client";
import { cn } from "@/lib/utils";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface EncryptedTextProps {
    text: string;
    interval?: number;
    className?: string;
    revealedClassName?: string;
}

const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";

export const EncryptedText = ({
    text,
    interval = 40,
    className,
    revealedClassName,
}: EncryptedTextProps) => {
    const [outputText, setOutputText] = useState("");
    const [isMounted, setIsMounted] = useState(false);

    useEffect(() => {
        setIsMounted(true);
    }, []);

    useEffect(() => {
        if (!isMounted) return;

        // Start with scrambled text
        setOutputText(
            text.split("").map(c => c === " " ? " " : chars[Math.floor(Math.random() * chars.length)]).join("")
        );

        let iteration = 0;
        const totalIterations = text.length * 2;

        const timer = setInterval(() => {
            setOutputText(
                text.split("").map((letter, index) => {
                    if (letter === " ") return " ";
                    if (index < iteration / 2) {
                        return text[index];
                    }
                    return chars[Math.floor(Math.random() * chars.length)];
                }).join("")
            );

            iteration++;

            if (iteration >= totalIterations) {
                setOutputText(text);
                clearInterval(timer);
            }
        }, interval);

        return () => clearInterval(timer);
    }, [text, interval, isMounted]);

    if (!isMounted) {
        return (
            <span className={cn("inline-block", className)}>
                <span className={cn("opacity-0", revealedClassName)}>{text}</span>
            </span>
        );
    }

    return (
        <motion.span
            className={cn("inline-block", className)}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
        >
            <span className={cn("transition-colors duration-300", revealedClassName)}>{outputText}</span>
        </motion.span>
    );
};
