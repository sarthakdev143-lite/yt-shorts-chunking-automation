import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

export const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-full border text-sm font-semibold transition duration-200 disabled:pointer-events-none disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]/40",
  {
    variants: {
      variant: {
        primary:
          "border-[color:var(--accent)] bg-[color:var(--accent)] px-5 py-2.5 text-[color:var(--accent-foreground)] shadow-[0_18px_40px_rgba(68,190,163,0.24)] hover:-translate-y-0.5 hover:bg-[color:var(--accent-strong)]",
        secondary:
          "border-[color:var(--line)] bg-white/5 px-5 py-2.5 text-[color:var(--foreground)] hover:border-[color:var(--accent)]/60 hover:bg-white/8",
        ghost:
          "border-transparent bg-transparent px-3 py-2 text-[color:var(--muted-foreground)] hover:bg-white/6 hover:text-[color:var(--foreground)]",
        danger:
          "border-[#7d2c2c] bg-[#7d2c2c]/20 px-5 py-2.5 text-[#ffd8d8] hover:bg-[#7d2c2c]/35",
      },
      size: {
        sm: "h-9 px-4 text-xs",
        md: "h-11 px-5",
        lg: "h-12 px-6 text-sm",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, type = "button", ...props }, ref) => (
    <button
      className={cn(buttonVariants({ variant, size }), className)}
      ref={ref}
      type={type}
      {...props}
    />
  ),
);

Button.displayName = "Button";
