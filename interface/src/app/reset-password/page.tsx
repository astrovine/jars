"use client";

import React, { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useResetPassword } from "@/hooks/use-queries";
import { motion } from "framer-motion";
import { Eye, EyeOff, ArrowLeft, CheckCircle, AlertCircle, Check, X } from "lucide-react";

function ResetPasswordContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const token = searchParams.get("token") || "";

    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

    const { mutate: resetPassword, isPending } = useResetPassword({
        onSuccess: () => {
            setSuccess(true);
            setTimeout(() => router.push("/login?password_reset=true"), 2000);
        },
        onError: (error) => setError(error.message),
    });

    // Password validation (matching backend)
    const hasMinLength = password.length >= 8;
    const hasUppercase = /[A-Z]/.test(password);
    const hasLowercase = /[a-z]/.test(password);
    const hasNumber = /\d/.test(password);
    const isPasswordValid = hasMinLength && hasUppercase && hasLowercase && hasNumber;
    const passwordsMatch = password === confirmPassword && confirmPassword.length > 0;

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!isPasswordValid) {
            setError("Please meet all password requirements");
            return;
        }

        if (!passwordsMatch) {
            setError("Passwords don't match");
            return;
        }

        if (!token) {
            setError("Invalid reset link");
            return;
        }

        resetPassword({ token, newPassword: password });
    };

    const PasswordRule = ({ met, label }: { met: boolean; label: string }) => (
        <div className={`flex items-center gap-1.5 text-xs ${met ? 'text-emerald-400' : 'text-neutral-600'}`}>
            {met ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
            {label}
        </div>
    );

    if (!token) {
        return (
            <div className="min-h-screen bg-[#09090b] flex flex-col">
                <header className="p-6 lg:p-8">
                    <Link href="/">
                        <span className="text-xl font-semibold text-white tracking-tight">jars</span>
                    </Link>
                </header>
                <main className="flex-1 flex items-center justify-center px-4">
                    <div className="text-center">
                        <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                        <h1 className="text-xl font-semibold text-white mb-2">Invalid reset link</h1>
                        <p className="text-sm text-neutral-500 mb-6">
                            This password reset link is invalid or has expired.
                        </p>
                        <Link
                            href="/forgot-password"
                            className="text-sm text-white hover:underline"
                        >
                            Request a new link
                        </Link>
                    </div>
                </main>
            </div>
        );
    }

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
                        {!success ? (
                            <>
                                {/* Header */}
                                <div className="text-center mb-8">
                                    <h1 className="text-2xl font-semibold text-white mb-2">
                                        Set new password
                                    </h1>
                                    <p className="text-sm text-neutral-500">
                                        Choose a strong password for your account
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
                                    {/* New Password */}
                                    <div>
                                        <label className="block text-sm font-medium text-neutral-400 mb-1.5">
                                            New password
                                        </label>
                                        <div className="relative">
                                            <input
                                                type={showPassword ? "text" : "password"}
                                                required
                                                value={password}
                                                onChange={(e) => setPassword(e.target.value)}
                                                className="w-full h-11 px-3 pr-10 bg-[#141417] border border-[#27272a] rounded-lg text-white text-sm placeholder:text-neutral-600 focus:outline-none focus:border-neutral-600 transition-colors"
                                                placeholder="••••••••"
                                            />
                                            <button
                                                type="button"
                                                onClick={() => setShowPassword(!showPassword)}
                                                className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-600 hover:text-neutral-400"
                                            >
                                                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                            </button>
                                        </div>
                                        {password && (
                                            <div className="mt-2 grid grid-cols-2 gap-1">
                                                <PasswordRule met={hasMinLength} label="8+ chars" />
                                                <PasswordRule met={hasUppercase} label="Uppercase" />
                                                <PasswordRule met={hasLowercase} label="Lowercase" />
                                                <PasswordRule met={hasNumber} label="Number" />
                                            </div>
                                        )}
                                    </div>

                                    {/* Confirm Password */}
                                    <div>
                                        <label className="block text-sm font-medium text-neutral-400 mb-1.5">
                                            Confirm password
                                        </label>
                                        <div className="relative">
                                            <input
                                                type={showConfirmPassword ? "text" : "password"}
                                                required
                                                value={confirmPassword}
                                                onChange={(e) => setConfirmPassword(e.target.value)}
                                                className={`w-full h-11 px-3 pr-10 bg-[#141417] border rounded-lg text-white text-sm placeholder:text-neutral-600 focus:outline-none transition-colors ${confirmPassword.length > 0
                                                        ? passwordsMatch
                                                            ? 'border-emerald-500/50'
                                                            : 'border-red-500/50'
                                                        : 'border-[#27272a] focus:border-neutral-600'
                                                    }`}
                                                placeholder="••••••••"
                                            />
                                            <button
                                                type="button"
                                                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                                className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-600 hover:text-neutral-400"
                                            >
                                                {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                            </button>
                                        </div>
                                    </div>

                                    <button
                                        type="submit"
                                        disabled={isPending || !isPasswordValid || !passwordsMatch}
                                        className="w-full h-11 bg-white hover:bg-neutral-100 text-black font-medium text-sm rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        {isPending ? "Resetting..." : "Reset password"}
                                    </button>
                                </form>
                            </>
                        ) : (
                            <>
                                {/* Success State */}
                                <div className="text-center">
                                    <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto mb-4">
                                        <CheckCircle className="w-5 h-5 text-emerald-400" />
                                    </div>
                                    <h1 className="text-2xl font-semibold text-white mb-2">
                                        Password reset
                                    </h1>
                                    <p className="text-sm text-neutral-500">
                                        Redirecting you to sign in...
                                    </p>
                                </div>
                            </>
                        )}
                    </motion.div>
                </div>
            </main>
        </div>
    );
}

export default function ResetPasswordPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-[#09090b] flex items-center justify-center">
                <div className="w-6 h-6 border-2 border-neutral-800 border-t-white rounded-full animate-spin" />
            </div>
        }>
            <ResetPasswordContent />
        </Suspense>
    );
}
