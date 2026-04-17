import * as React from "react";

import { cn } from "@/lib/utils";

export function Textarea({ className, ...props }: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cn(
        "min-h-28 w-full rounded-2xl border border-[color:var(--line)] bg-black/20 px-4 py-3 text-sm leading-6 text-[color:var(--foreground)] outline-none transition placeholder:text-[color:var(--muted-foreground)] focus:border-[color:var(--accent)]/70 focus:bg-black/28",
        className,
      )}
      {...props}
    />
  );
}
