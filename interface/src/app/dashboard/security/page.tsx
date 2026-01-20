"use client";

import React, { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/dashboard/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useAuthStore } from "@/lib/stores";
import { usePauseAllSubscriptions, useExchangeKeys, useRevokeExchangeKey } from "@/hooks/use-queries";
import { cn } from "@/lib/utils";
import {
  Shield,
  ShieldAlert,
  ShieldCheck,
  ShieldOff,
  Key,
  Lock,
  Smartphone,
  AlertOctagon,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Eye,
  EyeOff,
  LogOut,
  Trash2,
  Info,
  ExternalLink,
  Copy,
  Loader2
} from "lucide-react";
import { QRCodeSVG } from "qrcode.react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { authAPI } from "@/lib/api";

export default function SecurityPage() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();

  const [show2FADialog, setShow2FADialog] = useState(false);
  const [showKillSwitchDialog, setShowKillSwitchDialog] = useState(false);
  const [showRevokeDialog, setShowRevokeDialog] = useState(false);
  const [confirmText, setConfirmText] = useState("");

  // 2FA State
  const [verificationCode, setVerificationCode] = useState("");

  const { data: keys } = useExchangeKeys();
  const { mutate: pauseAll, isPending: isPausing } = usePauseAllSubscriptions();
  const { mutate: revokeKey, isPending: isRevoking } = useRevokeExchangeKey();

  const activeKeys = keys?.filter((k) => k.is_active) || [];

  // 2FA Mutations
  const { mutate: setup2FA, data: setupData, isPending: isLoadingSetup, reset: resetSetup } = useMutation({
    mutationFn: async () => {
      return await authAPI.setup2FA();
    }
  });

  const { mutate: confirm2FA, isPending: isConfirming2FA, error: confirmError, reset: resetConfirm } = useMutation({
    mutationFn: async (data: { secret: string; code: string }) => {
      return await authAPI.confirm2FA(data.secret, data.code);
    },
    onSuccess: () => {
      setShow2FADialog(false);
      setVerificationCode("");
      resetSetup();
      queryClient.invalidateQueries({ queryKey: ["user"] });
    }
  });

  // Handle Dialog Open
  useEffect(() => {
    if (show2FADialog && !user?.is2faEnabled && !setupData) {
      setup2FA();
    }
  }, [show2FADialog, user?.is2faEnabled, setupData, setup2FA]);

  const handleCopySecret = () => {
    if (setupData?.secret) {
      navigator.clipboard.writeText(setupData.secret);
    }
  };

  const handleVerify2FA = () => {
    if (setupData?.secret && verificationCode.length === 6) {
      confirm2FA({ secret: setupData.secret, code: verificationCode });
    }
  };

  const handleKillSwitch = () => {
    pauseAll(undefined, {
      onSuccess: () => {
        setShowKillSwitchDialog(false);
        setConfirmText("");
      },
    });
  };

  const handleRevokeAllKeys = () => {
    activeKeys.forEach((key) => {
      revokeKey(key.id);
    });
    setShowRevokeDialog(false);
    setConfirmText("");
  };

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-4xl">
        {/* Page Header */}
        <div>
          <h1 className="text-2xl font-semibold text-white">
            Security
          </h1>
          <p className="text-sm text-neutral-400 mt-1">
            Manage your account security and emergency controls
          </p>
        </div>

        {/* Kill Switch - Most Important */}
        <Card className="border-red-500/30 bg-red-950/10">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-red-500/20 flex items-center justify-center">
                <AlertOctagon className="w-6 h-6 text-red-500" />
              </div>
              <div>
                <CardTitle className="text-red-500">
                  Emergency Kill Switch
                </CardTitle>
                <CardDescription className="text-red-200/60">
                  Instantly stop all trading activity across all copied traders
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-neutral-400 mb-4">
              Use this if you need to immediately stop all copy trading. This
              will pause all active subscriptions. Your existing positions will
              remain open, but no new trades will be executed.
            </p>
            <Button
              variant="destructive"
              size="lg"
              className="w-full sm:w-auto"
              onClick={() => setShowKillSwitchDialog(true)}
            >
              <AlertOctagon className="w-5 h-5 mr-2" />
              Pause All Trading
            </Button>
          </CardContent>
        </Card>

        {/* API Key Revocation */}
        <Card className="border-amber-500/30">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center">
                <Key className="w-6 h-6 text-amber-500" />
              </div>
              <div>
                <CardTitle>Revoke All API Keys</CardTitle>
                <CardDescription>
                  Disconnect all exchange connections permanently
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-sm text-neutral-400">
                  You have {activeKeys.length} active API key
                  {activeKeys.length !== 1 ? "s" : ""} connected.
                </p>
              </div>
              <Badge
                variant={activeKeys.length > 0 ? "secondary" : "outline"}
                className={cn("text-xs", activeKeys.length > 0 ? "bg-emerald-500/20 text-emerald-500" : "")}
              >
                {activeKeys.length} Active
              </Badge>
            </div>
            <Button
              variant="outline"
              className="border-amber-500 text-amber-500 hover:bg-amber-500/10"
              onClick={() => setShowRevokeDialog(true)}
              disabled={activeKeys.length === 0}
            >
              <ShieldOff className="w-4 h-4 mr-2" />
              Revoke All Keys
            </Button>
          </CardContent>
        </Card>

        <Separator className="bg-white/10" />

        {/* Two-Factor Authentication */}
        <Card className="bg-[#0A0A0C] border-white/10">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                  <Smartphone className="w-6 h-6 text-emerald-500" />
                </div>
                <div>
                  <CardTitle className="text-white">Two-Factor Authentication</CardTitle>
                  <CardDescription>
                    Add an extra layer of security to your account
                  </CardDescription>
                </div>
              </div>
              <Badge
                variant={user?.is2faEnabled ? "secondary" : "destructive"}
                className={cn("text-xs", user?.is2faEnabled ? "bg-emerald-500/20 text-emerald-500" : "bg-amber-500/20 text-amber-500")}
              >
                {user?.is2faEnabled ? "Enabled" : "Disabled"}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <p className="text-sm text-neutral-400">
                {user?.is2faEnabled
                  ? "Your account is protected with 2FA"
                  : "Enable 2FA to protect your account from unauthorized access"}
              </p>
              <Button
                variant={user?.is2faEnabled ? "outline" : "default"}
                onClick={() => setShow2FADialog(true)}
                className={cn(!user?.is2faEnabled && "bg-emerald-600 hover:bg-emerald-700 text-white")}
              >
                {user?.is2faEnabled ? "Manage 2FA" : "Enable 2FA"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Password */}
        <Card className="bg-[#0A0A0C] border-white/10">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center">
                <Lock className="w-6 h-6 text-neutral-400" />
              </div>
              <div>
                <CardTitle className="text-white">Password</CardTitle>
                <CardDescription>
                  Change your account password
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Button variant="outline" className="border-white/10 text-neutral-300 hover:bg-white/5">Change Password</Button>
          </CardContent>
        </Card>

        {/* Active Sessions */}
        <Card className="bg-[#0A0A0C] border-white/10">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center">
                <Shield className="w-6 h-6 text-neutral-400" />
              </div>
              <div>
                <CardTitle className="text-white">Active Sessions</CardTitle>
                <CardDescription>
                  Manage devices where you are logged in
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/5">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-emerald-500" />
                  <div>
                    <p className="text-sm font-medium text-white">
                      Current Session
                    </p>
                    <p className="text-xs text-neutral-400">
                      Windows - Chrome - Active now
                    </p>
                  </div>
                </div>
                <Badge variant="secondary" className="text-[9px] bg-emerald-500/20 text-emerald-500">
                  Current
                </Badge>
              </div>
            </div>
            <Button variant="outline" className="mt-4 border-white/10 text-neutral-300 hover:bg-white/5">
              <LogOut className="w-4 h-4 mr-2" />
              Log Out All Devices
            </Button>
          </CardContent>
        </Card>

        {/* 2FA Setup Dialog */}
        <Dialog open={show2FADialog} onOpenChange={(open) => {
          if (!open) {
            setVerificationCode("");
            resetSetup();
            resetConfirm();
          }
          setShow2FADialog(open);
        }}>
          <DialogContent className="bg-[#111] border-white/10 text-white sm:max-w-md">
            <DialogHeader>
              <DialogTitle className="text-xl">Set up Two-Factor Authentication</DialogTitle>
              <DialogDescription className="text-neutral-400">
                Use an authenticator app (like Google Authenticator) to scan the QR code below.
              </DialogDescription>
            </DialogHeader>

            {isLoadingSetup ? (
              <div className="flex flex-col items-center justify-center py-8">
                <Loader2 className="w-8 h-8 text-emerald-500 animate-spin mb-4" />
                <p className="text-sm text-neutral-400">Generating secret...</p>
              </div>
            ) : setupData ? (
              <div className="flex flex-col items-center py-4 space-y-6">
                <div className="p-4 bg-white rounded-lg">
                  <QRCodeSVG value={setupData.qr_code_uri} size={180} />
                </div>

                <div className="w-full space-y-2">
                  <div className="flex items-center justify-between text-xs text-neutral-500 uppercase tracking-wider">
                    <span>Manual Entry Key</span>
                    <button onClick={handleCopySecret} className="flex items-center hover:text-white transition-colors">
                      <Copy className="w-3 h-3 mr-1" /> Copy
                    </button>
                  </div>
                  <div className="p-3 bg-white/5 border border-white/10 rounded font-mono text-center text-emerald-500 tracking-widest">
                    {setupData.secret}
                  </div>
                </div>

                <div className="w-full space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm text-neutral-400">Enter the 6-digit code from your app</label>
                    <Input
                      className="bg-black border-white/10 text-center font-mono text-lg tracking-[0.5em] h-12"
                      placeholder="000000"
                      maxLength={6}
                      value={verificationCode}
                      onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    />
                  </div>

                  {confirmError && (
                    <div className="p-2 bg-red-500/10 border border-red-500/20 rounded text-xs text-red-500 flex items-center gap-2">
                      <AlertTriangle className="w-3 h-3" />
                      Invalid code. Please try again.
                    </div>
                  )}

                  <Button
                    className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-medium"
                    onClick={handleVerify2FA}
                    disabled={verificationCode.length !== 6 || isConfirming2FA}
                  >
                    {isConfirming2FA ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Verifying...
                      </>
                    ) : "Verify & Enable"}
                  </Button>
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-red-500">
                Error loading 2FA setup. Please try again.
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Kill Switch Dialog */}
        <Dialog open={showKillSwitchDialog} onOpenChange={setShowKillSwitchDialog}>
          <DialogContent className="bg-[#111] border-red-500/30 text-white">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-red-500">
                <AlertOctagon className="w-5 h-5" />
                Emergency Kill Switch
              </DialogTitle>
              <DialogDescription className="text-neutral-400">
                This will immediately pause all active copy trading subscriptions.
              </DialogDescription>
            </DialogHeader>

            <div className="py-4">
              <div className="p-4 rounded-lg bg-red-950/20 border border-red-500/20 mb-4">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-red-200/80">
                    <p className="font-medium text-red-500 mb-1">
                      Warning: This action will:
                    </p>
                    <ul className="list-disc list-inside space-y-1">
                      <li>Pause all active copy trading subscriptions</li>
                      <li>Stop executing any new trades</li>
                      <li>Leave existing positions open</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-neutral-300">
                  Type &quot;PAUSE ALL&quot; to confirm
                </label>
                <Input
                  value={confirmText}
                  onChange={(e) => setConfirmText(e.target.value)}
                  placeholder="PAUSE ALL"
                  className="font-mono bg-black border-white/10"
                />
              </div>
            </div>

            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setShowKillSwitchDialog(false);
                  setConfirmText("");
                }}
                className="border-white/10 text-white hover:bg-white/5"
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={handleKillSwitch}
                disabled={confirmText !== "PAUSE ALL"}
              >
                Pause All Trading
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Revoke All Keys Dialog */}
        <Dialog open={showRevokeDialog} onOpenChange={setShowRevokeDialog}>
          <DialogContent className="bg-[#111] border-amber-500/30 text-white">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-amber-500">
                <ShieldOff className="w-5 h-5" />
                Revoke All API Keys
              </DialogTitle>
              <DialogDescription className="text-neutral-400">
                This will disconnect all exchange API keys from your account.
              </DialogDescription>
            </DialogHeader>

            <div className="py-4">
              <div className="p-4 rounded-lg bg-amber-950/20 border border-amber-500/20 mb-4">
                <div className="flex items-start gap-3">
                  <Info className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-amber-200/80">
                    <p>
                      After revoking, you will need to create new API keys on
                      your exchange to continue trading.
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-neutral-300">
                  Type &quot;REVOKE ALL&quot; to confirm
                </label>
                <Input
                  value={confirmText}
                  onChange={(e) => setConfirmText(e.target.value)}
                  placeholder="REVOKE ALL"
                  className="font-mono bg-black border-white/10"
                />
              </div>
            </div>

            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setShowRevokeDialog(false);
                  setConfirmText("");
                }}
                className="border-white/10 text-white hover:bg-white/5"
              >
                Cancel
              </Button>
              <Button
                className="bg-amber-600 hover:bg-amber-700 text-white border-none"
                onClick={handleRevokeAllKeys}
                disabled={confirmText !== "REVOKE ALL"}
              >
                Revoke All Keys
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
