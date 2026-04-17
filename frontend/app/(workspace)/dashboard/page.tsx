import { ActivitySquare } from "lucide-react";

import { MetricCard } from "@/components/metric-card";
import { ProjectCard } from "@/components/project-card";
import { UploadWizard } from "@/components/upload-wizard";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getDashboardSnapshot } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";

export default async function DashboardPage() {
  const overview = await getDashboardSnapshot();

  return (
    <div className="space-y-6">
      <UploadWizard />

      <section className="grid gap-4 xl:grid-cols-4">
        <MetricCard
          detail="Projects actively tracked across upload, review, and scheduling surfaces."
          label="Projects"
          value={overview.summary.totalProjects.toString()}
        />
        <MetricCard
          detail="Chunks approved for queue placement after review."
          label="Approved"
          value={overview.summary.approvedChunks.toString()}
        />
        <MetricCard
          detail="Segments waiting on review or reprocessing."
          label="Pending"
          value={overview.summary.pendingChunks.toString()}
        />
        <MetricCard
          detail="Already published to YouTube and cleaned from temporary storage."
          label="Uploaded"
          value={overview.summary.uploadedChunks.toString()}
        />
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
        <div className="grid gap-6 lg:grid-cols-2">
          {overview.projects.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>

        <Card className="h-full">
          <CardHeader>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--accent)]">
              <ActivitySquare className="h-4 w-4" />
              Activity stream
            </div>
            <CardTitle className="mt-3 text-2xl">Live processing signals</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {overview.activity.map((item) => (
              <div className="rounded-2xl border border-white/6 bg-black/12 p-4" key={item.id}>
                <div className="flex items-center justify-between gap-3">
                  <Badge variant={item.kind === "processing" ? "warning" : item.kind === "upload" ? "accent" : "neutral"}>
                    {item.kind}
                  </Badge>
                  <p className="text-xs font-medium uppercase tracking-[0.18em] text-[color:var(--muted-foreground)]">
                    {formatDateTime(item.timestamp)}
                  </p>
                </div>
                <p className="mt-3 text-sm leading-6 text-[color:var(--foreground)]">{item.label}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
