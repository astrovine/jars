"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRegister, useVerifyEmail } from "@/hooks/use-queries";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AlertCircle, Mail, Key, Eye, EyeOff } from "lucide-react";

// OAuth Icons
const GoogleIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24">
    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
  </svg>
);

const MicrosoftIcon = () => (
  <svg width="20" height="20" viewBox="0 0 23 23">
    <rect x="1" y="1" width="10" height="10" fill="#F25022" />
    <rect x="12" y="1" width="10" height="10" fill="#7FBA00" />
    <rect x="1" y="12" width="10" height="10" fill="#00A4EF" />
    <rect x="12" y="12" width="10" height="10" fill="#FFB900" />
  </svg>
);

type RegisterView = "form" | "verify";

const countries = [
  { code: "NG", name: "Nigeria" },
  { code: "GH", name: "Ghana" },
  { code: "KE", name: "Kenya" },
  { code: "ZA", name: "South Africa" },
  { code: "EG", name: "Egypt" },
  { code: "US", name: "United States" },
  { code: "GB", name: "United Kingdom" },
  { code: "CA", name: "Canada" },
  { code: "AE", name: "United Arab Emirates" },
];

export default function RegisterPage() {
  const router = useRouter();
  const [view, setView] = useState<RegisterView>("form");
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    firstName: "",
    lastName: "",
    email: "",
    country: "NG",
    password: "",
  });
  const [error, setError] = useState<string | null>(null);

  // Dev Mode for token input
  const [devMode, setDevMode] = useState(false);
  const [devToken, setDevToken] = useState("");
  const [verificationCode, setVerificationCode] = useState(["", "", "", "", "", ""]);

  const { mutate: register, isPending: isRegistering } = useRegister({
    onSuccess: () => setView("verify"),
    onError: (error) => setError(error.message),
  });

  const { mutate: verifyEmail, isPending: isVerifying } = useVerifyEmail({
    onSuccess: () => router.push("/login?verified=true"),
    onError: (error) => setError(error.message),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (formData.password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    register({
      email: formData.email,
      password: formData.password,
      first_name: formData.firstName,
      last_name: formData.lastName,
      country: formData.country,
    });
  };

  const handleCodeInput = (index: number, value: string) => {
    if (value.length > 1) value = value[0];
    if (!/^\d?$/.test(value)) return;
    const newCode = [...verificationCode];
    newCode[index] = value;
    setVerificationCode(newCode);
    if (value && index < 5) {
      document.getElementById(`code-${index + 1}`)?.focus();
    }
  };

  const handleVerifySubmit = () => {
    const token = devMode ? devToken : verificationCode.join("");
    if (token) {
      verifyEmail(token);
    }
  };

  return (
    <div className="relative min-h-screen w-full bg-black flex items-center justify-center p-4 overflow-auto">
      {/* Grid Background */}
      <div
        className={cn(
          "absolute inset-0",
          "[background-size:40px_40px]",
          "[background-image:linear-gradient(to_right,#262626_1px,transparent_1px),linear-gradient(to_bottom,#262626_1px,transparent_1px)]"
        )}
      />
      {/* Radial gradient for faded look */}
      <div className="pointer-events-none absolute inset-0 bg-black [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black)]" />

      <AnimatePresence mode="wait">
        {view === "form" ? (
          <motion.div
            key="form"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="relative z-10 w-full max-w-md"
          >
            {/* Card */}
            <div className="bg-[#191919] rounded-xl border border-[#333] p-6 shadow-2xl">
              {/* Logo */}
              <div className="flex items-center justify-center mb-5">
                <Link href="/" className="text-xl font-bold text-white">
                  jars_
                </Link>
              </div>

              {/* Header */}
              <h1 className="text-lg font-medium text-white text-center mb-5">
                Create your account
              </h1>

              {/* Error */}
              {error && (
                <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-md flex items-center gap-2 text-sm text-red-400">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  {error}
                </div>
              )}

              {/* OAuth Buttons */}
              <div className="space-y-2 mb-5">
                <button
                  type="button"
                  className="w-full h-9 rounded-md bg-[#252525] border border-[#404040] text-white text-sm flex items-center justify-center gap-2 hover:bg-[#303030] transition-colors"
                >
                  <GoogleIcon />
                  Continue with Google
                </button>
                <button
                  type="button"
                  className="w-full h-9 rounded-md bg-[#252525] border border-[#404040] text-white text-sm flex items-center justify-center gap-2 hover:bg-[#303030] transition-colors"
                >
                  <MicrosoftIcon />
                  Continue with Microsoft
                </button>
                <button
                  type="button"
                  className="w-full h-9 rounded-md bg-[#252525] border border-[#404040] text-white text-sm flex items-center justify-center gap-2 hover:bg-[#303030] transition-colors"
                >
                  <Key className="w-4 h-4" />
                  Continue with Passkey
                </button>
              </div>

              {/* Divider */}
              <div className="relative my-5">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-[#404040]" />
                </div>
                <div className="relative flex justify-center">
                  <span className="px-3 bg-[#191919] text-xs text-[#888]">
                    or continue with email
                  </span>
                </div>
              </div>

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-3">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-xs text-[#888] mb-1">First name</label>
                    <Input
                      className="h-9 bg-[#252525] border-[#404040] text-white text-sm"
                      required
                      value={formData.firstName}
                      onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-[#888] mb-1">Last name</label>
                    <Input
                      className="h-9 bg-[#252525] border-[#404040] text-white text-sm"
                      required
                      value={formData.lastName}
                      onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs text-[#888] mb-1">Email</label>
                  <Input
                    type="email"
                    className="h-9 bg-[#252525] border-[#404040] text-white text-sm"
                    placeholder="you@example.com"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  />
                </div>

                <div>
                  <label className="block text-xs text-[#888] mb-1">Country</label>
                  <select
                    value={formData.country}
                    onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                    className="flex h-9 w-full rounded-md border border-[#404040] bg-[#252525] px-3 py-1 text-sm text-white"
                  >
                    {countries.map((c) => (
                      <option key={c.code} value={c.code} className="bg-[#252525]">
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs text-[#888] mb-1">Password</label>
                  <div className="relative">
                    <Input
                      type={showPassword ? "text" : "password"}
                      className="h-9 bg-[#252525] border-[#404040] text-white text-sm pr-9"
                      placeholder="Min 8 characters"
                      required
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-[#666] hover:text-white"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <Button
                  type="submit"
                  disabled={isRegistering}
                  className="w-full h-9 bg-emerald-600 hover:bg-emerald-700 text-white font-medium mt-2"
                >
                  {isRegistering ? "Creating account..." : "Continue"}
                </Button>
              </form>

              {/* Terms */}
              <p className="text-[10px] text-[#666] text-center mt-3">
                By continuing, you agree to our{" "}
                <Link href="/terms" className="text-emerald-500 hover:underline">Terms</Link>
                {" "}and{" "}
                <Link href="/privacy" className="text-emerald-500 hover:underline">Privacy Policy</Link>
              </p>

              {/* Login Link */}
              <p className="text-center text-xs text-[#888] mt-4">
                Already have an account?{" "}
                <Link href="/login" className="text-emerald-500 hover:text-emerald-400">
                  Sign in
                </Link>
              </p>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="verify"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="relative z-10 w-full max-w-md"
          >
            {/* Email Verification Card */}
            <div className="bg-[#191919] rounded-xl border border-[#333] p-6 shadow-2xl text-center">
              <div className="w-14 h-14 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto mb-5">
                <Mail className="w-7 h-7 text-emerald-400" />
              </div>

              <h1 className="text-lg font-medium text-white mb-2">Check your email</h1>
              <p className="text-sm text-[#888] mb-5">
                We sent a verification link to{" "}
                <span className="text-emerald-400">{formData.email}</span>
              </p>

              {error && (
                <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-md flex items-center gap-2 text-sm text-red-400">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  {error}
                </div>
              )}

              {!devMode ? (
                <div className="flex justify-center gap-2 mb-5">
                  {verificationCode.map((digit, i) => (
                    <Input
                      key={i}
                      id={`code-${i}`}
                      type="text"
                      inputMode="numeric"
                      maxLength={1}
                      value={digit}
                      onChange={(e) => handleCodeInput(i, e.target.value)}
                      className="w-9 h-11 bg-[#252525] border-[#404040] text-center text-lg font-bold text-white"
                    />
                  ))}
                </div>
              ) : (
                <div className="mb-5">
                  <textarea
                    value={devToken}
                    onChange={(e) => setDevToken(e.target.value)}
                    placeholder="Paste verification token..."
                    className="w-full h-16 p-2 bg-[#252525] border border-[#404040] rounded-md text-xs font-mono text-white resize-none"
                  />
                </div>
              )}

              <Button
                onClick={handleVerifySubmit}
                disabled={isVerifying}
                className="w-full h-9 bg-emerald-600 hover:bg-emerald-700 text-white font-medium mb-3"
              >
                {isVerifying ? "Verifying..." : "Verify Email"}
              </Button>

              <button
                type="button"
                onClick={() => setDevMode(!devMode)}
                className="text-xs text-[#666] hover:text-[#888]"
              >
                {devMode ? "Switch to code entry" : "Dev: Enter token manually"}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
