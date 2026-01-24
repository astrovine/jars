"use client";

import React, { useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useVerifyEmail } from "@/hooks/use-queries";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useResendVerification } from "@/hooks/use-queries";
import { useState } from "react";
import { CheckCircle, AlertCircle, Loader2, ArrowRight } from "lucide-react";

function VerifyEmailContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const token = searchParams.get("token") || "";

    // Resend state
    const [email, setEmail] = useState("");
    const { mutate: resend, isPending: isResending, isSuccess: resendSuccess, isError: resendError, error: resendErrorMsg } = useResendVerification();

    const handleResend = (e: React.FormEvent) => {
        e.preventDefault();
        if (email) resend(email);
    };

    const { mutate: verifyEmail, isPending, isSuccess, isError, error } = useVerifyEmail({
        onSuccess: () => {
            setTimeout(() => router.push("/login?verified=true"), 2000);
        },
    });

    useEffect(() => {
        if (token) {
            verifyEmail(token);
        }
    }, [token, verifyEmail]);

    // Shared Resend Form Component
    const ResendForm = () => (
        <div className="mt-8 pt-8 border-t border-white/10 w-full max-w-sm mx-auto">
            <h3 className="text-sm font-medium text-white mb-3">Need a new verification link?</h3>
            {resendSuccess ? (
                <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-3 text-emerald-400 text-sm flex items-center gap-2">
                    <CheckCircle className="w-4 h-4" />
                    <span>Link sent! Check your email.</span>
                </div>
            ) : (
                <form onSubmit={handleResend} className="flex gap-2">
                    <Input
                        type="email"
                        placeholder="Enter your email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="bg-white/5 border-white/10 text-white placeholder:text-neutral-500 focus-visible:ring-emerald-500/50"
                        required
                    />
                    <Button
                        type="submit"
                        disabled={isResending}
                        className="bg-white text-black hover:bg-neutral-200 font-medium"
                    >
                        {isResending ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
                    </Button>
                </form>
            )}
            {resendError && (
                <p className="text-xs text-red-400 mt-2 text-left">
                    {resendErrorMsg?.message || "Failed to send link. Please try again."}
                </p>
            )}
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
                    <div className="text-center w-full max-w-md">
                        <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                        <h1 className="text-xl font-semibold text-white mb-2">Invalid verification link</h1>
                        <p className="text-sm text-neutral-500 mb-6">
                            This verification link is invalid or has expired.
                        </p>
                        <Link
                            href="/login"
                            className="text-sm text-white hover:underline block mb-6"
                        >
                            Go to sign in
                        </Link>

                        <ResendForm />
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
            <main className="flex-1 flex items-center justify-center px-4">
                <div className="text-center w-full max-w-md">
                    {isPending && (
                        <>
                            <Loader2 className="w-12 h-12 text-white mx-auto mb-4 animate-spin" />
                            <h1 className="text-xl font-semibold text-white mb-2">Verifying your email...</h1>
                            <p className="text-sm text-neutral-500">
                                Please wait while we confirm your email address.
                            </p>
                        </>
                    )}

                    {isSuccess && (
                        <>
                            <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto mb-4">
                                <CheckCircle className="w-6 h-6 text-emerald-400" />
                            </div>
                            <h1 className="text-xl font-semibold text-white mb-2">Email verified!</h1>
                            <p className="text-sm text-neutral-500">
                                Redirecting you to sign in...
                            </p>
                        </>
                    )}

                    {isError && (
                        <>
                            <div className="w-12 h-12 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto mb-4">
                                <AlertCircle className="w-6 h-6 text-red-400" />
                            </div>
                            <h1 className="text-xl font-semibold text-white mb-2">Verification failed</h1>
                            <p className="text-sm text-neutral-500 mb-6">
                                {error?.message || "This link may have expired or already been used."}
                            </p>
                            <Link
                                href="/login"
                                className="text-sm text-white hover:underline block mb-6"
                            >
                                Go to sign in
                            </Link>

                            <ResendForm />
                        </>
                    )}
                </div>
            </main>
        </div>
    );
}

export default function VerifyEmailPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-[#09090b] flex items-center justify-center">
                <div className="w-6 h-6 border-2 border-neutral-800 border-t-white rounded-full animate-spin" />
            </div>
        }>
            <VerifyEmailContent />
        </Suspense>
    );
}
