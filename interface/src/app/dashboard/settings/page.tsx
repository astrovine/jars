"use client";

import React, { useState } from "react";
import { DashboardLayout } from "@/components/dashboard/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { useAuthStore } from "@/lib/stores";
import { cn } from "@/lib/utils";
import {
  User,
  Mail,
  Globe,
  Bell,
  Moon,
  Monitor,
  Palette,
  Volume2,
  VolumeX,
  Save,
  RefreshCw,
} from "lucide-react";

interface SettingRowProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  children: React.ReactNode;
}

function SettingRow({ icon, title, description, children }: SettingRowProps) {
  return (
    <div className="flex items-center justify-between py-4">
      <div className="flex items-start gap-4">
        <div className="w-10 h-10 rounded-lg bg-[var(--background-muted)] flex items-center justify-center flex-shrink-0">
          {icon}
        </div>
        <div>
          <h4 className="text-sm font-medium text-[var(--foreground)]">
            {title}
          </h4>
          <p className="text-xs text-[var(--foreground-muted)] mt-0.5">
            {description}
          </p>
        </div>
      </div>
      <div className="flex-shrink-0">{children}</div>
    </div>
  );
}

export default function SettingsPage() {
  const { user } = useAuthStore();
  const [isDirty, setIsDirty] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Form state
  const [firstName, setFirstName] = useState(user?.firstName || "");
  const [lastName, setLastName] = useState(user?.lastName || "");
  const [email, setEmail] = useState(user?.email || "");

  // Preferences
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [tradeAlerts, setTradeAlerts] = useState(true);
  const [soundEnabled, setSoundEnabled] = useState(false);
  const [timezone, setTimezone] = useState("UTC");

  const handleSave = async () => {
    setIsSaving(true);
    // API call here
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsSaving(false);
    setIsDirty(false);
  };

  const handleChange = () => {
    setIsDirty(true);
  };

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-4xl">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-[var(--foreground)]">
              Settings
            </h1>
            <p className="text-sm text-[var(--foreground-muted)] mt-1">
              Manage your account settings and preferences
            </p>
          </div>
          {isDirty && (
            <Button onClick={handleSave} loading={isSaving}>
              <Save className="w-4 h-4 mr-2" />
              Save Changes
            </Button>
          )}
        </div>

        {/* Profile Settings */}
        <Card>
          <CardHeader>
            <CardTitle>Profile Information</CardTitle>
            <CardDescription>
              Update your personal details and public profile
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-[var(--foreground)]">
                  First Name
                </label>
                <Input
                  value={firstName}
                  onChange={(e) => {
                    setFirstName(e.target.value);
                    handleChange();
                  }}
                  icon={<User className="w-4 h-4" />}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-[var(--foreground)]">
                  Last Name
                </label>
                <Input
                  value={lastName}
                  onChange={(e) => {
                    setLastName(e.target.value);
                    handleChange();
                  }}
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-[var(--foreground)]">
                Email
              </label>
              <Input
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  handleChange();
                }}
                icon={<Mail className="w-4 h-4" />}
              />
              <p className="text-xs text-[var(--foreground-muted)]">
                Changing your email will require verification
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Notification Preferences */}
        <Card>
          <CardHeader>
            <CardTitle>Notifications</CardTitle>
            <CardDescription>
              Configure how you receive notifications
            </CardDescription>
          </CardHeader>
          <CardContent className="divide-y divide-[var(--border)]">
            <SettingRow
              icon={<Mail className="w-5 h-5 text-[var(--foreground-muted)]" />}
              title="Email Notifications"
              description="Receive email updates about your account and trades"
            >
              <Switch
                checked={emailNotifications}
                onCheckedChange={(checked) => {
                  setEmailNotifications(checked);
                  handleChange();
                }}
              />
            </SettingRow>

            <SettingRow
              icon={<Bell className="w-5 h-5 text-[var(--foreground-muted)]" />}
              title="Trade Alerts"
              description="Get notified when trades are executed"
            >
              <Switch
                checked={tradeAlerts}
                onCheckedChange={(checked) => {
                  setTradeAlerts(checked);
                  handleChange();
                }}
              />
            </SettingRow>

            <SettingRow
              icon={
                soundEnabled ? (
                  <Volume2 className="w-5 h-5 text-[var(--foreground-muted)]" />
                ) : (
                  <VolumeX className="w-5 h-5 text-[var(--foreground-muted)]" />
                )
              }
              title="Sound Effects"
              description="Play sounds for notifications and trade execution"
            >
              <Switch
                checked={soundEnabled}
                onCheckedChange={(checked) => {
                  setSoundEnabled(checked);
                  handleChange();
                }}
              />
            </SettingRow>
          </CardContent>
        </Card>

        {/* Display Preferences */}
        <Card>
          <CardHeader>
            <CardTitle>Display</CardTitle>
            <CardDescription>
              Customize the appearance of the dashboard
            </CardDescription>
          </CardHeader>
          <CardContent className="divide-y divide-[var(--border)]">
            <SettingRow
              icon={<Moon className="w-5 h-5 text-[var(--foreground-muted)]" />}
              title="Theme"
              description="JARS uses a professional dark theme optimized for trading"
            >
              <div className="flex items-center gap-2 text-sm text-[var(--foreground-muted)]">
                <Moon className="w-4 h-4" />
                Dark Mode (Default)
              </div>
            </SettingRow>

            <SettingRow
              icon={<Globe className="w-5 h-5 text-[var(--foreground-muted)]" />}
              title="Timezone"
              description="All times will be displayed in this timezone"
            >
              <select
                value={timezone}
                onChange={(e) => {
                  setTimezone(e.target.value);
                  handleChange();
                }}
                className="h-9 rounded-md border border-[var(--border)] bg-[var(--background-elevated)] px-3 text-sm text-[var(--foreground)]"
              >
                <option value="UTC">UTC</option>
                <option value="America/New_York">Eastern Time</option>
                <option value="America/Los_Angeles">Pacific Time</option>
                <option value="Europe/London">London</option>
                <option value="Asia/Tokyo">Tokyo</option>
                <option value="Asia/Singapore">Singapore</option>
              </select>
            </SettingRow>

            <SettingRow
              icon={<Monitor className="w-5 h-5 text-[var(--foreground-muted)]" />}
              title="Data Density"
              description="Adjust how compact the interface appears"
            >
              <div className="flex items-center gap-2 text-sm text-[var(--foreground-muted)]">
                High Density (Default)
              </div>
            </SettingRow>
          </CardContent>
        </Card>

        {/* Trading Defaults */}
        <Card>
          <CardHeader>
            <CardTitle>Trading Defaults</CardTitle>
            <CardDescription>
              Set default values for new copy trading subscriptions
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-[var(--foreground)]">
                  Default Allocation (%)
                </label>
                <Input
                  type="number"
                  defaultValue="10"
                  min={1}
                  max={100}
                  suffix={<span className="text-[var(--foreground-muted)]">%</span>}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-[var(--foreground)]">
                  Default Stop Loss (%)
                </label>
                <Input
                  type="number"
                  defaultValue="5"
                  min={1}
                  max={50}
                  suffix={<span className="text-[var(--foreground-muted)]">%</span>}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-[var(--foreground)]">
                  Default Take Profit (%)
                </label>
                <Input
                  type="number"
                  defaultValue="10"
                  min={1}
                  max={100}
                  suffix={<span className="text-[var(--foreground-muted)]">%</span>}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Danger Zone */}
        <Card className="border-[var(--danger)]/30">
          <CardHeader>
            <CardTitle className="text-[var(--danger)]">Danger Zone</CardTitle>
            <CardDescription>
              Irreversible actions - please proceed with caution
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-4 rounded-lg border border-[var(--border)]">
              <div>
                <h4 className="text-sm font-medium text-[var(--foreground)]">
                  Export Data
                </h4>
                <p className="text-xs text-[var(--foreground-muted)]">
                  Download all your data including trades, ledger, and settings
                </p>
              </div>
              <Button variant="outline" size="sm">
                Export
              </Button>
            </div>

            <div className="flex items-center justify-between p-4 rounded-lg border border-[var(--danger)]/30 bg-[var(--danger-subtle)]">
              <div>
                <h4 className="text-sm font-medium text-[var(--danger)]">
                  Delete Account
                </h4>
                <p className="text-xs text-[var(--foreground-muted)]">
                  Permanently delete your account and all associated data
                </p>
              </div>
              <Button variant="destructive" size="sm">
                Delete Account
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}

