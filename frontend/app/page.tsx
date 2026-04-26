import Link from "next/link";
import { cookies } from "next/headers";
import { ArrowRight, Blocks, CloudUpload, ShieldCheck, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getDashboardSnapshot, getPlatformHealth } from "@/lib/api";
import { createClient as createSupabaseServerClient, hasSupabaseConfig } from "@/utils/supabase/server";
import { cn } from "@/lib/utils";

const pillars = [
  {
    icon: CloudUpload,
    title: "Google Drive transit storage",
    body: "Source files land in Google Drive before processing, keeping the pipeline simpler to operate locally.",
  },
  {
    icon: Sparkles,
    title: "Serial FFmpeg pipeline",
    body: "Chunk splitting, reframing, subtitle burn-in, and thumbnail extraction are processed one chunk at a time.",
  },
  {
    icon: ShieldCheck,
    title: "Temporary storage policy",
    body: "Raw chunks are deleted after processing, and final Shorts are deleted after successful YouTube upload.",
  },
  {
    icon: Blocks,
    title: "Review before publish",
    body: "Every chunk exposes subtitle, metadata, trim, thumbnail, and reframe controls before it reaches the queue.",
  },
];

export default async function HomePage() {
  const supabaseEnabled = hasSupabaseConfig();
  const todosPromise = supabaseEnabled
    ? (async () => {
        const cookieStore = await cookies();
        const supabase = createSupabaseServerClient(cookieStore);
        const result = await supabase.from("todos").select("id, name").limit(5);
        return result.error ? [] : result.data ?? [];
      })()
    : Promise.resolve([]);
  const [overview, health, todos] = await Promise.all([getDashboardSnapshot(), getPlatformHealth(), todosPromise]);

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(68,190,163,0.22),transparent_28%),radial-gradient(circle_at_85%_12%,rgba(242,168,72,0.14),transparent_22%),linear-gradient(180deg,rgba(255,255,255,0.02),rgba(255,255,255,0))]" />
      <main className="relative mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 py-6 sm:px-8 lg:py-10">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-(--line) pb-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.26em] text-(--accent)">Shortsmith</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
              Production-minded Shorts chunking without paid infra.
            </h1>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link className={cn(buttonVariants({ variant: "primary" }), "min-w-40")} href="/dashboard">
              Open dashboard
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
            <Link className={cn(buttonVariants({ variant: "secondary" }), "min-w-40")} href="/settings">
              View settings
            </Link>
          </div>
        </div>

        <section className="grid flex-1 items-center gap-10 py-10 lg:grid-cols-[1.05fr_0.95fr]">
          <div className="space-y-8">
            <Badge variant={health.mode === "demo" ? "accent" : "success"}>
              {health.mode === "demo" ? "Seeded demo mode" : "Live backend connected"}
            </Badge>
            <div className="space-y-5">
              <h2 className="max-w-4xl text-5xl font-semibold leading-tight tracking-tight text-[color:var(--foreground)] sm:text-6xl">
                Chunk long-form video, review every Short, then schedule YouTube uploads with cleanup built in.
              </h2>
              <p className="max-w-2xl text-lg leading-8 text-[color:var(--muted-foreground)]">
                Next.js drives the operator UI, FastAPI and Celery process the footage, Groq handles transcription,
                and Google Drive acts as a temporary transit layer so the workflow stays operational without dedicated object storage.
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <Card>
                <CardHeader>
                  <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--muted-foreground)]">Projects</p>
                  <CardTitle className="mt-3 text-4xl">{overview.summary.totalProjects}</CardTitle>
                </CardHeader>
              </Card>
              <Card>
                <CardHeader>
                  <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--muted-foreground)]">Approved chunks</p>
                  <CardTitle className="mt-3 text-4xl">{overview.summary.approvedChunks}</CardTitle>
                </CardHeader>
              </Card>
              <Card>
                <CardHeader>
                  <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--muted-foreground)]">Uploaded</p>
                  <CardTitle className="mt-3 text-4xl">{overview.summary.uploadedChunks}</CardTitle>
                </CardHeader>
              </Card>
            </div>

            {todos.length > 0 ? (
              <Card>
                <CardHeader>
                  <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--muted-foreground)]">
                    Supabase todos
                  </p>
                  <CardTitle className="mt-3 text-2xl">Live sample query</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-sm text-[color:var(--muted-foreground)]">
                    {todos.map((todo) => (
                      <li key={todo.id}>{todo.name}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ) : null}
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {pillars.map((pillar) => {
              const Icon = pillar.icon;
              return (
                <Card key={pillar.title}>
                  <CardHeader>
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-[color:var(--accent)]/20 bg-[color:var(--accent)]/10">
                      <Icon className="h-5 w-5 text-[color:var(--accent)]" />
                    </div>
                    <CardTitle className="mt-4 text-2xl">{pillar.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm leading-6 text-[color:var(--muted-foreground)]">{pillar.body}</p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </section>
      </main>
    </div>
  );
}
