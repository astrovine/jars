import * as React from "react";
import { cn } from "@/lib/utils";

const Badge = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    variant?:
      | "default"
      | "success"
      | "warning"
      | "danger"
      | "outline"
      | "verified"
      | "incubation";
  }
>(({ className, variant = "default", ...props }, ref) => {
  const variants = {
    default:
      "bg-[var(--primary-subtle)] text-[var(--primary)] border-transparent",
    success:
      "bg-[var(--success-subtle)] text-[var(--success-text)] border-transparent",
    warning:
      "bg-[var(--warning-subtle)] text-[var(--warning-text)] border-transparent",
    danger:
      "bg-[var(--danger-subtle)] text-[var(--danger-text)] border-transparent",
    outline:
      "bg-transparent text-[var(--foreground-muted)] border-[var(--border)]",
    verified:
      "bg-gradient-to-r from-[rgba(212,165,116,0.2)] to-[rgba(212,165,116,0.1)] text-[var(--accent)] border-[rgba(212,165,116,0.3)]",
    incubation:
      "bg-[var(--background-muted)] text-[var(--foreground-subtle)] border-[var(--border)]",
  };

  return (
    <div
      ref={ref}
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:ring-offset-2",
        variants[variant],
        className
      )}
      {...props}
    />
  );
});
Badge.displayName = "Badge";

export { Badge };

