"use client";

import React, { useEffect, useState } from "react";
import { useSystemStore, type ConnectionStatus } from "@/lib/stores";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import {
  Activity,
  Zap,
  Wallet,
  Clock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Loader2,
} from "lucide-react";

interface StatusIndicatorProps {
  label: string;
  status: ConnectionStatus;
  icon: React.ReactNode;
  detail?: string;
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  label,
  status,
  icon,
  detail,
}) => {
  const statusConfig: Record<ConnectionStatus, {
    color: string;
    bgColor: string;
    pulseClass: string;
    text: string;
    Icon: React.ElementType;
  }> = {
    connected: {
      color: "text-[#22C55E]",
      bgColor: "bg-[#22C55E]",
      pulseClass: "animate-pulse",
      text: "Connected",
      Icon: CheckCircle,
    },
    connecting: {
      color: "text-[#D4A574]",
      bgColor: "bg-[#D4A574]",
      pulseClass: "animate-pulse",
      text: "Connecting",
      Icon: Loader2,
    },
    disconnected: {
      color: "text-[#525252]",
      bgColor: "bg-[#525252]",
      pulseClass: "",
      text: "Disconnected",
      Icon: XCircle,
    },
    error: {
      color: "text-[#EF4444]",
      bgColor: "bg-[#EF4444]",
      pulseClass: "animate-pulse",
      text: "Error",
      Icon: AlertTriangle,
    },
  };

  const config = statusConfig[status];

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md hover:bg-[#1a1a1a] transition-colors cursor-default">
          <div className="flex items-center gap-1.5">
            <span className="text-[#737373]">{icon}</span>
            <span className="text-xs font-medium text-[#737373]">
              {label}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <div
              className={cn(
                "w-2 h-2 rounded-full",
                config.bgColor,
                config.pulseClass
              )}
            />
            <span className={cn("text-xs font-medium", config.color)}>
              {config.text}
            </span>
          </div>
        </div>
      </TooltipTrigger>
      <TooltipContent side="bottom" className="bg-[#1a1a1a] border-[#262626]">
        <div className="text-xs">
          <p className="font-medium text-[#ededed]">{label}</p>
          <p className="text-[#737373]">{detail || config.text}</p>
        </div>
      </TooltipContent>
    </Tooltip>
  );
};

interface LatencyDisplayProps {
  label: string;
  value: number;
  unit?: string;
  threshold?: { warning: number; critical: number };
}

const LatencyDisplay: React.FC<LatencyDisplayProps> = ({
  label,
  value,
  unit = "ms",
  threshold = { warning: 100, critical: 500 },
}) => {
  const getLatencyColor = () => {
    if (value === 0) return "text-[#525252]";
    if (value <= threshold.warning) return "text-[#22C55E]";
    if (value <= threshold.critical) return "text-[#D4A574]";
    return "text-[#EF4444]";
  };

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md hover:bg-[#1a1a1a] transition-colors cursor-default">
          <span className="text-xs text-[#737373]">{label}:</span>
          <span
            className={cn(
              "text-xs font-mono font-medium tabular-nums",
              getLatencyColor()
            )}
          >
            {value > 0 ? `${value}${unit}` : "—"}
          </span>
        </div>
      </TooltipTrigger>
      <TooltipContent side="bottom" className="bg-[#1a1a1a] border-[#262626]">
        <div className="text-xs">
          <p className="font-medium text-[#ededed]">{label}</p>
          <p className="text-[#737373]">
            {value > 0
              ? value <= threshold.warning
                ? "Optimal performance"
                : value <= threshold.critical
                ? "Slight delay"
                : "High latency"
              : "Not measured"}
          </p>
        </div>
      </TooltipContent>
    </Tooltip>
  );
};

export function SystemHealthBar() {
  const { health } = useSystemStore();
  const [currentTime, setCurrentTime] = useState<string>("");

  // Update time every second
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(
        now.toLocaleTimeString("en-US", {
          hour12: false,
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          timeZone: "UTC",
        }) + " UTC"
      );
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);

    return () => clearInterval(interval);
  }, []);

  // Overall system status
  const overallStatus: ConnectionStatus =
    health.sentinel === "connected" &&
    health.exchange === "connected" &&
    health.wallet === "connected"
      ? "connected"
      : health.sentinel === "error" ||
        health.exchange === "error" ||
        health.wallet === "error"
      ? "error"
      : health.sentinel === "connecting" ||
        health.exchange === "connecting" ||
        health.wallet === "connecting"
      ? "connecting"
      : "disconnected";

  return (
    <div className="h-10 bg-[#080808] border-b border-[#1a1a1a] px-4 flex items-center justify-between">
      {/* Left: System Status Indicators */}
      <div className="flex items-center gap-1">
        <StatusIndicator
          label="API"
          status={health.sentinel}
          icon={<Activity className="w-3.5 h-3.5" />}
          detail="Backend API connection"
        />
        <div className="w-px h-4 bg-[#1a1a1a]" />
        <StatusIndicator
          label="Exchange"
          status={health.exchange}
          icon={<Zap className="w-3.5 h-3.5" />}
          detail="Exchange connectivity"
        />
        <div className="w-px h-4 bg-[#1a1a1a]" />
        <StatusIndicator
          label="Wallet"
          status={health.wallet}
          icon={<Wallet className="w-3.5 h-3.5" />}
          detail="Wallet sync status"
        />
      </div>

      {/* Right: Latency & Time */}
      <div className="flex items-center gap-1">
        <LatencyDisplay
          label="Latency"
          value={health.executionLatency}
          threshold={{ warning: 50, critical: 200 }}
        />
        <div className="w-px h-4 bg-[#1a1a1a]" />
        <div className="flex items-center gap-2 px-3 py-1.5">
          <Clock className="w-3.5 h-3.5 text-[#525252]" />
          <span className="text-xs font-mono text-[#737373] tabular-nums">
            {currentTime}
          </span>
        </div>
      </div>
    </div>
  );
}

