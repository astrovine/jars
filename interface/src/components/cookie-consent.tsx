"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";

const COOKIE_CONSENT_KEY = "jars-cookie-consent";

export function CookieConsent() {
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        // Check if user has already consented
        const consent = localStorage.getItem(COOKIE_CONSENT_KEY);
        if (!consent) {
            // Small delay before showing
            const timer = setTimeout(() => setIsVisible(true), 1500);
            return () => clearTimeout(timer);
        }
    }, []);

    const handleAcceptAll = () => {
        localStorage.setItem(COOKIE_CONSENT_KEY, JSON.stringify({
            essential: true,
            analytics: true,
            marketing: true,
            timestamp: new Date().toISOString()
        }));
        setIsVisible(false);
    };

    const handleDecline = () => {
        localStorage.setItem(COOKIE_CONSENT_KEY, JSON.stringify({
            essential: true,
            analytics: false,
            marketing: false,
            timestamp: new Date().toISOString()
        }));
        setIsVisible(false);
    };

    return (
        <AnimatePresence>
            {isVisible && (
                <motion.div
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    exit={{ y: 20, opacity: 0 }}
                    transition={{ type: "spring", damping: 25, stiffness: 300 }}
                    className="fixed bottom-4 left-4 z-[100] max-w-sm"
                >
                    <div className="bg-[#1a1a1a] border border-white/10 rounded-lg p-4 shadow-xl shadow-black/20">
                        {/* Close button */}
                        <button
                            onClick={handleDecline}
                            className="absolute top-2 right-2 text-white/30 hover:text-white/60 transition-colors"
                        >
                            <X className="w-4 h-4" />
                        </button>

                        <p className="text-xs text-white/60 pr-4 mb-3 leading-relaxed">
                            We use cookies to improve your experience.{" "}
                            <a href="/privacy" className="text-emerald-400 hover:underline">
                                Learn more
                            </a>
                        </p>

                        <div className="flex gap-2">
                            <button
                                onClick={handleDecline}
                                className="px-3 py-1.5 text-xs text-white/60 hover:text-white transition-colors"
                            >
                                Decline
                            </button>
                            <button
                                onClick={handleAcceptAll}
                                className="px-4 py-1.5 bg-white text-black text-xs font-medium rounded hover:bg-white/90 transition-colors"
                            >
                                Accept
                            </button>
                        </div>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}

export default CookieConsent;
