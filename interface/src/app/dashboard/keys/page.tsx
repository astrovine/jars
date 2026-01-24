"use client";

import React, { useState } from "react";
import { DashboardLayout } from "@/components/dashboard/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { useExchangeKeys, useCreateExchangeKey, useRevokeExchangeKey } from "@/hooks/use-queries";
import { cn } from "@/lib/utils";
import type { ExchangeName } from "@/types";
import {
  Key,
  Plus,
  Shield,
  ShieldCheck,
  Trash2,
  Eye,
  EyeOff,
  AlertTriangle,
} from "lucide-react";

const exchanges: { value: ExchangeName; label: string; color: string }[] = [
  { value: "binance", label: "Binance", color: "bg-[#F3BA2F]" },
  { value: "bybit", label: "Bybit", color: "bg-[#F7A600]" },
  { value: "okx", label: "OKX", color: "bg-white" },
];

export default function KeysPage() {
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedKeyId, setSelectedKeyId] = useState<string | null>(null);

  // Form state
  const [exchange, setExchange] = useState<ExchangeName>("binance");
  const [label, setLabel] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [apiSecret, setApiSecret] = useState("");
  const [showSecret, setShowSecret] = useState(false);

  const { data: keys, isLoading } = useExchangeKeys();
  const { mutate: createKey, isPending: isCreating } = useCreateExchangeKey({
    onSuccess: () => {
      setShowAddDialog(false);
      resetForm();
    },
  });
  const { mutate: revokeKey, isPending: isRevoking } = useRevokeExchangeKey({
    onSuccess: () => {
      setShowDeleteDialog(false);
      setSelectedKeyId(null);
    },
  });

  const resetForm = () => {
    setLabel("");
    setApiKey("");
    setApiSecret("");
    setShowSecret(false);
  };

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    createKey({
      exchange_name: exchange,
      label,
      api_key: apiKey,
      api_secret: apiSecret,
    });
  };

  const handleDelete = () => {
    if (selectedKeyId) {
      revokeKey(selectedKeyId);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-[#ededed]">API Keys</h1>
            <p className="text-sm text-[#737373] mt-1">
              Connect your exchange accounts for copy trading
            </p>
          </div>
          <Button
            onClick={() => setShowAddDialog(true)}
            className="bg-[#3B82F6] hover:bg-[#2563EB]"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Key
          </Button>
        </div>

        {/* Security Notice */}
        <Card className="bg-[#3B82F6]/5 border-[#3B82F6]/20">
          <CardContent className="py-4">
            <div className="flex items-start gap-4">
              <Shield className="w-5 h-5 text-[#3B82F6] flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm text-[#ededed] font-medium">
                  Your API keys are encrypted with AES-256
                </p>
                <p className="text-sm text-[#737373] mt-1">
                  We only request trade permissions. Withdrawal permissions are never required.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Keys List */}
        {isLoading ? (
          <div className="space-y-4">
            {[1, 2].map((i) => (
              <Skeleton key={i} className="h-32 bg-[#262626] rounded-xl" />
            ))}
          </div>
        ) : !keys || keys.length === 0 ? (
          <Card className="bg-[#111111] border-[#1a1a1a]">
            <CardContent className="py-12 text-center">
              <Key className="w-12 h-12 text-[#525252] mx-auto mb-4" />
              <h3 className="text-lg font-medium text-[#ededed] mb-2">
                No API keys connected
              </h3>
              <p className="text-[#737373] mb-4">
                Connect your exchange to start copy trading
              </p>
              <Button
                onClick={() => setShowAddDialog(true)}
                className="bg-[#3B82F6] hover:bg-[#2563EB]"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Your First Key
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {keys.map((key) => {
              const exchangeInfo = exchanges.find((e) => e.value === key.exchange_name);
              return (
                <Card key={key.id} className="bg-[#111111] border-[#1a1a1a]">
                  <CardContent className="p-5">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-4">
                        <div
                          className={cn(
                            "w-12 h-12 rounded-xl flex items-center justify-center font-bold",
                            exchangeInfo?.color || "bg-[#262626]"
                          )}
                        >
                          {key.exchange_name.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold text-[#ededed]">
                              {key.label}
                            </h3>
                            {key.is_active && key.is_valid ? (
                              <Badge variant="success" className="text-[9px]">
                                Active
                              </Badge>
                            ) : (
                              <Badge variant="danger" className="text-[9px]">
                                Invalid
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm text-[#737373]">
                            {exchangeInfo?.label || key.exchange_name}
                          </p>
                          <code className="text-xs text-[#525252] font-mono mt-2 block">
                            {key.api_key_masked}
                          </code>
                        </div>
                      </div>

                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setSelectedKeyId(key.id);
                          setShowDeleteDialog(true);
                        }}
                        className="text-[#EF4444] hover:text-[#EF4444] hover:bg-[#EF4444]/10"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>

                    {/* Permissions */}
                    <div className="mt-4 flex flex-wrap gap-2">
                      {key.permissions.map((perm) => (
                        <Badge
                          key={perm}
                          variant="outline"
                          className="text-[10px] border-[#262626] text-[#737373]"
                        >
                          {perm}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}

        {/* Add Key Dialog */}
        <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
          <DialogContent className="bg-[#111111] border-[#1a1a1a]">
            <DialogHeader>
              <DialogTitle className="text-[#ededed]">Add API Key</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreate} className="space-y-4">
              {/* Exchange Selection */}
              <div className="space-y-2">
                <label className="text-sm text-[#ededed]">Exchange</label>
                <div className="grid grid-cols-3 gap-2">
                  {exchanges.map((ex) => (
                    <button
                      key={ex.value}
                      type="button"
                      onClick={() => setExchange(ex.value)}
                      className={cn(
                        "p-3 rounded-lg border text-center transition-colors",
                        exchange === ex.value
                          ? "border-[#3B82F6] bg-[#3B82F6]/10"
                          : "border-[#262626] hover:border-[#3B82F6]/50"
                      )}
                    >
                      <span className="text-sm font-medium text-[#ededed]">
                        {ex.label}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Label */}
              <div className="space-y-2">
                <label className="text-sm text-[#ededed]">Label</label>
                <Input
                  placeholder="e.g., Main Trading Account"
                  value={label}
                  onChange={(e) => setLabel(e.target.value)}
                  className="bg-[#0A0A0A] border-[#262626] text-[#ededed]"
                  required
                />
              </div>

              {/* API Key */}
              <div className="space-y-2">
                <label className="text-sm text-[#ededed]">API Key</label>
                <Input
                  placeholder="Enter your API key"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="bg-[#0A0A0A] border-[#262626] text-[#ededed] font-mono"
                  required
                />
              </div>

              {/* API Secret */}
              <div className="space-y-2">
                <label className="text-sm text-[#ededed]">API Secret</label>
                <div className="relative">
                  <Input
                    type={showSecret ? "text" : "password"}
                    placeholder="Enter your API secret"
                    value={apiSecret}
                    onChange={(e) => setApiSecret(e.target.value)}
                    className="bg-[#0A0A0A] border-[#262626] text-[#ededed] font-mono pr-10"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowSecret(!showSecret)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[#525252] hover:text-[#a1a1a1]"
                  >
                    {showSecret ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowAddDialog(false)}
                  className="border-[#262626]"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  className="bg-[#3B82F6] hover:bg-[#2563EB]"
                  disabled={isCreating}
                >
                  {isCreating ? "Adding..." : "Add Key"}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* Delete Confirmation Dialog */}
        <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
          <DialogContent className="bg-[#111111] border-[#1a1a1a]">
            <DialogHeader>
              <DialogTitle className="text-[#ededed] flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-[#EF4444]" />
                Revoke API Key?
              </DialogTitle>
            </DialogHeader>
            <p className="text-[#737373]">
              This will permanently disconnect this exchange account.
              Any active copy trading using this key will be stopped.
            </p>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setShowDeleteDialog(false)}
                className="border-[#262626]"
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={handleDelete}
                disabled={isRevoking}
              >
                {isRevoking ? "Revoking..." : "Revoke Key"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}

