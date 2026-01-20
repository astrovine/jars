"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useForgotPassword } from "@/hooks/use-queries";
import { motion } from "framer-motion";
import { ArrowLeft, Mail, CheckCircle, AlertCircle } from "lucide-react";

export default function ForgotPasswordPage() {
    const [email, setEmail] = useState("");
    const [submitted, setSubmitted] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const { mutate: forgotPassword, isPending } = useForgotPassword({
        onSuccess: () => setSubmitted(true),
        onError: (error) => setError(error.message),
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        forgotPassword(email);
    };

    return (
        <div className="min-h-screen bg-[#09090b] flex flex-col">
            {/* Header */}
            <header className="p-6 lg:p-8">
                <Link href="/">
                    <span className="text-xl font-semibold text-white tracking-tight">jars</span>
                </Link>
            </header>

            {/* Main */}
            <main className="flex-1 flex items-center justify-center px-4 pb-12">
                <div className="w-full max-w-sm">
                    <motion.div
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.15 }}
                    >
                        {!submitted ? (
                            <>
                                {/* Header */}
                                <div className="text-center mb-8">
                                    <h1 className="text-2xl font-semibold text-white mb-2">
                                        Reset password
                                    </h1>
                                    <p className="text-sm text-neutral-500">
                                        Enter your email and we'll send you a reset link
                                    </p>
                                </div>

                                {/* Error */}
                                {error && (
                                    <div className="mb-5 p-3 border border-red-500/20 bg-red-500/5 rounded-lg flex items-center gap-2 text-sm text-red-400">
                                        <AlertCircle className="w-4 h-4 flex-shrink-0" />
                                        {error}
                                    </div>
                                )}

                                {/* Form */}
                                <form onSubmit={handleSubmit} className="space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium text-neutral-400 mb-1.5">
                                            Email address
                                        </label>
                                        <input
                                            type="email"
                                            required
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            className="w-full h-11 px-3 bg-[#141417] border border-[#27272a] rounded-lg text-white text-sm placeholder:text-neutral-600 focus:outline-none focus:border-neutral-600 transition-colors"
                                            placeholder="you@example.com"
                                        />
                                    </div>

                                    <button
                                        type="submit"
                                        disabled={isPending}
                                        className="w-full h-11 bg-white hover:bg-neutral-100 text-black font-medium text-sm rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        {isPending ? "Sending..." : "Send reset link"}
                                    </button>
                                </form>

                                {/* Back to login */}
                                <Link
                                    href="/login"
                                    className="mt-6 text-sm text-neutral-600 hover:text-neutral-400 flex items-center justify-center gap-1 transition-colors"
                                >
                                    <ArrowLeft className="w-4 h-4" />
                                    Back to sign in
                                </Link>
                            </>
                        ) : (
                            <>
                                {/* Success State */}
                                <div className="text-center">
                                    <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto mb-4">
                                        <Mail className="w-5 h-5 text-emerald-400" />
                                    </div>
                                    <h1 className="text-2xl font-semibold text-white mb-2">
                                        Check your email
                                    </h1>
                                    <p className="text-sm text-neutral-500 mb-6">
                                        If an account exists for <span className="text-white">{email}</span>, you'll receive a password reset link shortly.
                                    </p>

                                    <Link
                                        href="/login"
                                        className="inline-flex items-center gap-1 text-sm text-neutral-400 hover:text-white transition-colors"
                                    >
                                        <ArrowLeft className="w-4 h-4" />
                                        Back to sign in
                                    </Link>
                                </div>
                            </>
                        )}
                    </motion.div>
                </div>
            </main>
        </div>
    );
}
