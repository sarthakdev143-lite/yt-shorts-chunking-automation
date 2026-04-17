import Link from "next/link";
import { CalendarDays, Layers2, PlayCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { buttonVariants } from "@/components/ui/button";
import type { Project } from "@/lib/types";
import { cn, formatRelativeQueue } from "@/lib/utils";

const statusVariant: Record<Project["status"], "warning" | "success" | "accent" | "danger" | "neutral"> = {
  processing: "warning",
  ready: "success",
  scheduled: "accent",
  complete: "success",
  failed: "danger",
};

export function ProjectCard({ project }: { project: Project }) {
  const approved = project.chunks.filter((chunk) => chunk.status === "approved").length;
  const pending = project.chunks.filter((chunk) => chunk.status === "pending").length;

  return (
    <Card className="h-full overflow-hidden">
      <CardHeader className="gap-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Badge variant={statusVariant[project.status]}>{project.status}</Badge>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--muted-foreground)]">
            {project.privacy}
          </p>
        </div>
        <div>
          <CardTitle className="text-2xl">{project.name}</CardTitle>
          <p className="mt-2 text-sm leading-6 text-[color:var(--muted-foreground)]">{project.processingStage}</p>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-2xl border border-white/6 bg-black/12 p-4">
            <div className="flex items-center gap-2 text-sm text-[color:var(--muted-foreground)]">
              <Layers2 className="h-4 w-4" />
              Chunks
            </div>
            <p className="mt-3 text-2xl font-semibold text-[color:var(--foreground)]">{project.chunks.length}</p>
            <p className="mt-2 text-xs text-[color:var(--muted-foreground)]">{approved} approved, {pending} pending</p>
          </div>
          <div className="rounded-2xl border border-white/6 bg-black/12 p-4">
            <div className="flex items-center gap-2 text-sm text-[color:var(--muted-foreground)]">
              <PlayCircle className="h-4 w-4" />
              Queue
            </div>
            <p className="mt-3 text-2xl font-semibold text-[color:var(--foreground)]">{project.queueDepth}</p>
            <p className="mt-2 text-xs text-[color:var(--muted-foreground)]">Active Celery jobs</p>
          </div>
          <div className="rounded-2xl border border-white/6 bg-black/12 p-4">
            <div className="flex items-center gap-2 text-sm text-[color:var(--muted-foreground)]">
              <CalendarDays className="h-4 w-4" />
              Cadence
            </div>
            <p className="mt-3 text-lg font-semibold text-[color:var(--foreground)]">{formatRelativeQueue(project.dailyIntervalHours)}</p>
            <p className="mt-2 text-xs text-[color:var(--muted-foreground)]">Upload schedule mode</p>
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          <Link className={cn(buttonVariants({ variant: "primary" }), "min-w-40")} href={`/review/${project.id}`}>
            Open review
          </Link>
          <Link className={cn(buttonVariants({ variant: "secondary" }), "min-w-40")} href={`/scheduler/${project.id}`}>
            Open scheduler
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
