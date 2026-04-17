import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium uppercase tracking-[0.22em]",
  {
    variants: {
      variant: {
        neutral: "border-white/10 bg-white/6 text-[color:var(--muted-foreground)]",
        success: "border-emerald-400/20 bg-emerald-400/12 text-emerald-200",
        warning: "border-amber-400/20 bg-amber-400/12 text-amber-100",
        danger: "border-rose-400/20 bg-rose-400/12 text-rose-200",
        accent: "border-[color:var(--accent)]/30 bg-[color:var(--accent)]/12 text-[color:var(--accent)]",
      },
    },
    defaultVariants: {
      variant: "neutral",
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}
