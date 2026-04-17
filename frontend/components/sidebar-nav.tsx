"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { CalendarClock, FolderKanban, LayoutDashboard, Settings2 } from "lucide-react";

import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard", label: "Projects", icon: LayoutDashboard },
  { href: "/review/proj_founder-story", label: "Review", icon: FolderKanban },
  { href: "/scheduler/proj_founder-story", label: "Scheduler", icon: CalendarClock },
  { href: "/settings", label: "Settings", icon: Settings2 },
];

export function SidebarNav() {
  const pathname = usePathname();

  return (
    <aside className="sticky top-0 flex min-h-screen w-full max-w-72 flex-col justify-between border-r border-[color:var(--line)] bg-black/24 px-5 py-6 backdrop-blur-xl">
      <div className="space-y-8">
        <div className="space-y-3 rounded-[28px] border border-white/8 bg-[radial-gradient(circle_at_top_left,rgba(68,190,163,0.2),transparent_52%),rgba(8,11,18,0.86)] p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[color:var(--accent)]">Shortsmith</p>
          <h1 className="text-2xl font-semibold tracking-tight text-[color:var(--foreground)]">YouTube Shorts pipeline</h1>
          <p className="text-sm leading-6 text-[color:var(--muted-foreground)]">
            Upload once, process serially, review precisely, and clear temporary R2 assets immediately after publishing.
          </p>
        </div>

        <nav className="space-y-2">
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
            const Icon = item.icon;

            return (
              <Link
                className={cn(
                  "flex items-center gap-3 rounded-2xl border px-4 py-3 text-sm transition",
                  isActive
                    ? "border-[color:var(--accent)]/30 bg-[color:var(--accent)]/10 text-[color:var(--foreground)]"
                    : "border-transparent text-[color:var(--muted-foreground)] hover:border-white/8 hover:bg-white/5 hover:text-[color:var(--foreground)]",
                )}
                href={item.href}
                key={item.href}
              >
                <Icon className="h-4 w-4" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="rounded-[24px] border border-[color:var(--line)] bg-white/4 p-4 text-sm text-[color:var(--muted-foreground)]">
        <p className="font-medium text-[color:var(--foreground)]">Compliance</p>
        <p className="mt-2 leading-6">
          This workflow assumes the source footage is owned or explicitly licensed for redistribution.
        </p>
      </div>
    </aside>
  );
}
