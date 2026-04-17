import { BellDot } from "lucide-react";

import { ServerWakeIndicator } from "@/components/server-wake-indicator";

type TopbarProps = {
  userName?: string | null;
  userEmail?: string | null;
};

export function Topbar({ userName, userEmail }: TopbarProps) {
  return (
    <header className="sticky top-0 z-20 flex flex-col gap-4 border-b border-[color:var(--line)] bg-[color:var(--surface-elevated)]/85 px-4 py-4 backdrop-blur-xl sm:flex-row sm:items-center sm:justify-between sm:px-8">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.26em] text-[color:var(--accent)]">Workspace</p>
        <h2 className="mt-2 text-2xl font-semibold tracking-tight text-[color:var(--foreground)]">
          Review, refine, and release with a single queue.
        </h2>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <ServerWakeIndicator />
        <div className="flex items-center gap-3 rounded-full border border-[color:var(--line)] bg-white/4 px-4 py-2">
          <BellDot className="h-4 w-4 text-[color:var(--accent)]" />
          <div className="text-right text-xs leading-5 text-[color:var(--muted-foreground)]">
            <p className="font-medium text-[color:var(--foreground)]">{userName ?? "Connect Google"}</p>
            <p>{userEmail ?? "OAuth scopes sync to YouTube upload access"}</p>
          </div>
        </div>
      </div>
    </header>
  );
}
