import * as React from "react";

import { cn } from "@/lib/utils";

export function Input({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-12 w-full rounded-2xl border border-[color:var(--line)] bg-black/20 px-4 text-sm text-[color:var(--foreground)] outline-none transition placeholder:text-[color:var(--muted-foreground)] focus:border-[color:var(--accent)]/70 focus:bg-black/28",
        className,
      )}
      {...props}
    />
  );
}
