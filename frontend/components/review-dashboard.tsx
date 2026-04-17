"use client";

import Image from "next/image";
import { useMemo, useState } from "react";
import { Captions, CheckCheck, Crop, Film, ImageUp, Scissors, SkipForward } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import type { ChunkItem, Project, SubtitleCue } from "@/lib/types";
import { formatDateTime, formatDuration } from "@/lib/utils";

const thumbnailChoices = ["/demo/thumb-01.jpg", "/demo/thumb-02.jpg", "/demo/thumb-03.jpg"];

const chunkStatusVariant: Record<ChunkItem["status"], "warning" | "success" | "danger" | "accent"> = {
  pending: "warning",
  approved: "success",
  skipped: "danger",
  uploaded: "accent",
};

type ChunkCardProps = {
  chunk: ChunkItem;
  onChange: (chunkId: string, updater: (chunk: ChunkItem) => ChunkItem) => void;
  onStatusChange: (chunkId: string, status: ChunkItem["status"]) => void;
};

function CueEditor({ cue, onChange }: { cue: SubtitleCue; onChange: (cue: SubtitleCue) => void }) {
  return (
    <div className="rounded-2xl border border-white/6 bg-black/12 p-3">
      <div className="grid gap-3 sm:grid-cols-[110px_110px_minmax(0,1fr)]">
        <Input
          onChange={(event) => onChange({ ...cue, startSeconds: Number(event.target.value) || cue.startSeconds })}
          step="0.1"
          type="number"
          value={cue.startSeconds}
        />
        <Input
          onChange={(event) => onChange({ ...cue, endSeconds: Number(event.target.value) || cue.endSeconds })}
          step="0.1"
          type="number"
          value={cue.endSeconds}
        />
        <Textarea
          className="min-h-20"
          onChange={(event) => onChange({ ...cue, text: event.target.value })}
          value={cue.text}
        />
      </div>
    </div>
  );
}

export function ChunkCard({ chunk, onChange, onStatusChange }: ChunkCardProps) {
  return (
    <Card className="overflow-hidden">
      <CardHeader className="gap-4 border-b border-white/6 pb-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--muted-foreground)]">
              Chunk {chunk.order.toString().padStart(2, "0")}
            </p>
            <CardTitle className="mt-2 text-2xl">{chunk.title}</CardTitle>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={chunkStatusVariant[chunk.status]}>{chunk.status}</Badge>
            <Badge variant="neutral">{formatDuration(chunk.durationSeconds)}</Badge>
            <Badge variant={chunk.duplicateCheck.status === "duplicate" ? "danger" : "neutral"}>
              {chunk.duplicateCheck.status}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="grid gap-6 py-6 xl:grid-cols-[minmax(0,0.88fr)_minmax(0,1.12fr)]">
        <div className="space-y-5">
          <div className="overflow-hidden rounded-[28px] border border-white/6 bg-black/20">
            <video className="aspect-[9/16] w-full object-cover" controls poster={chunk.thumbnailUrl} preload="metadata" src={chunk.videoUrl} />
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-2xl border border-white/6 bg-black/12 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--muted-foreground)]">Trim</p>
              <p className="mt-3 text-lg font-semibold text-[color:var(--foreground)]">
                {chunk.trimRange.startSeconds}s - {chunk.trimRange.endSeconds}s
              </p>
            </div>
            <div className="rounded-2xl border border-white/6 bg-black/12 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--muted-foreground)]">Zoom</p>
              <p className="mt-3 text-lg font-semibold text-[color:var(--foreground)]">{chunk.reframe.zoom.toFixed(2)}x</p>
            </div>
            <div className="rounded-2xl border border-white/6 bg-black/12 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--muted-foreground)]">Schedule</p>
              <p className="mt-3 text-sm font-medium leading-6 text-[color:var(--foreground)]">{formatDateTime(chunk.scheduledFor)}</p>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <section className="space-y-3">
            <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.22em] text-[color:var(--muted-foreground)]">
              <Film className="h-4 w-4 text-[color:var(--accent)]" />
              Metadata editor
            </div>
            <div className="grid gap-3">
              <Input
                onChange={(event) => onChange(chunk.id, (current) => ({ ...current, title: event.target.value }))}
                value={chunk.title}
              />
              <Textarea
                onChange={(event) => onChange(chunk.id, (current) => ({ ...current, description: event.target.value }))}
                value={chunk.description}
              />
              <Input
                onChange={(event) =>
                  onChange(chunk.id, (current) => ({
                    ...current,
                    tags: event.target.value
                      .split(",")
                      .map((value) => value.trim())
                      .filter(Boolean),
                  }))
                }
                value={chunk.tags.join(", ")}
              />
            </div>
          </section>

          <section className="space-y-3">
            <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.22em] text-[color:var(--muted-foreground)]">
              <Captions className="h-4 w-4 text-[color:var(--accent)]" />
              Subtitle editor
            </div>
            <div className="space-y-3">
              {chunk.subtitleCues.map((cue) => (
                <CueEditor
                  cue={cue}
                  key={cue.id}
                  onChange={(updatedCue) =>
                    onChange(chunk.id, (current) => ({
                      ...current,
                      subtitleCues: current.subtitleCues.map((entry) =>
                        entry.id === updatedCue.id ? updatedCue : entry,
                      ),
                    }))
                  }
                />
              ))}
            </div>
          </section>

          <section className="grid gap-6 lg:grid-cols-2">
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.22em] text-[color:var(--muted-foreground)]">
                <ImageUp className="h-4 w-4 text-[color:var(--accent)]" />
                Thumbnail picker
              </div>
              <div className="grid grid-cols-3 gap-2">
                {thumbnailChoices.map((thumbnailUrl) => (
                    <button
                      className={`overflow-hidden rounded-2xl border transition ${
                        chunk.thumbnailUrl === thumbnailUrl
                          ? "border-[color:var(--accent)] shadow-[0_0_0_1px_rgba(68,190,163,0.4)]"
                          : "border-white/6 opacity-75 hover:opacity-100"
                      }`}
                    key={thumbnailUrl}
                    onClick={() => onChange(chunk.id, (current) => ({ ...current, thumbnailUrl }))}
                    type="button"
                  >
                      <Image
                        alt="Thumbnail candidate"
                        className="aspect-[9/16] w-full object-cover"
                        height={1920}
                        src={thumbnailUrl}
                        width={1080}
                      />
                    </button>
                ))}
              </div>
            </div>

            <div className="space-y-4">
              <div className="space-y-3 rounded-[24px] border border-white/6 bg-black/12 p-4">
                <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.22em] text-[color:var(--muted-foreground)]">
                  <Crop className="h-4 w-4 text-[color:var(--accent)]" />
                  Reframe controls
                </div>
                <label className="block text-sm text-[color:var(--muted-foreground)]">
                  Blur intensity: {chunk.reframe.blur}
                  <input
                    className="mt-2 w-full accent-[color:var(--accent)]"
                    max={40}
                    min={0}
                    onChange={(event) =>
                      onChange(chunk.id, (current) => ({
                        ...current,
                        reframe: { ...current.reframe, blur: Number(event.target.value) },
                      }))
                    }
                    type="range"
                    value={chunk.reframe.blur}
                  />
                </label>
                <label className="block text-sm text-[color:var(--muted-foreground)]">
                  Zoom level: {chunk.reframe.zoom.toFixed(2)}x
                  <input
                    className="mt-2 w-full accent-[color:var(--accent)]"
                    max={1.4}
                    min={1}
                    onChange={(event) =>
                      onChange(chunk.id, (current) => ({
                        ...current,
                        reframe: { ...current.reframe, zoom: Number(event.target.value) },
                      }))
                    }
                    step={0.01}
                    type="range"
                    value={chunk.reframe.zoom}
                  />
                </label>
              </div>

              <div className="space-y-3 rounded-[24px] border border-white/6 bg-black/12 p-4">
                <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.22em] text-[color:var(--muted-foreground)]">
                  <Scissors className="h-4 w-4 text-[color:var(--accent)]" />
                  Trim controls
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <Input
                    onChange={(event) =>
                      onChange(chunk.id, (current) => ({
                        ...current,
                        trimRange: { ...current.trimRange, startSeconds: Number(event.target.value) || 0 },
                      }))
                    }
                    type="number"
                    value={chunk.trimRange.startSeconds}
                  />
                  <Input
                    onChange={(event) =>
                      onChange(chunk.id, (current) => ({
                        ...current,
                        trimRange: { ...current.trimRange, endSeconds: Number(event.target.value) || current.trimRange.endSeconds },
                      }))
                    }
                    type="number"
                    value={chunk.trimRange.endSeconds}
                  />
                </div>
              </div>
            </div>
          </section>

          <div className="flex flex-wrap gap-3">
            <Button onClick={() => onStatusChange(chunk.id, "approved")} variant="primary">
              <CheckCheck className="mr-2 h-4 w-4" />
              Approve
            </Button>
            <Button onClick={() => onStatusChange(chunk.id, "skipped")} variant="danger">
              <SkipForward className="mr-2 h-4 w-4" />
              Skip
            </Button>
            <Button onClick={() => onStatusChange(chunk.id, "pending")} variant="secondary">
              Reset to pending
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function ReviewDashboard({ project }: { project: Project }) {
  const [chunks, setChunks] = useState(project.chunks);

  const summary = useMemo(
    () => ({
      approved: chunks.filter((chunk) => chunk.status === "approved").length,
      pending: chunks.filter((chunk) => chunk.status === "pending").length,
      skipped: chunks.filter((chunk) => chunk.status === "skipped").length,
      uploaded: chunks.filter((chunk) => chunk.status === "uploaded").length,
    }),
    [chunks],
  );

  function updateChunk(chunkId: string, updater: (chunk: ChunkItem) => ChunkItem) {
    setChunks((current) => current.map((chunk) => (chunk.id === chunkId ? updater(chunk) : chunk)));
  }

  function setAllStatus(status: ChunkItem["status"]) {
    setChunks((current) =>
      current.map((chunk) => (chunk.status === "uploaded" ? chunk : { ...chunk, status })),
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[color:var(--accent)]">Review dashboard</p>
            <CardTitle className="mt-3 text-3xl">{project.name}</CardTitle>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-[color:var(--muted-foreground)]">
              Edit subtitles against timestamps, adjust blur-and-zoom reframing, tune trim ranges, and approve only the chunks that survive editorial review.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button onClick={() => setAllStatus("approved")} variant="primary">
              Approve all
            </Button>
            <Button onClick={() => setAllStatus("skipped")} variant="secondary">
              Skip all
            </Button>
          </div>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-4">
          <div className="rounded-2xl border border-white/6 bg-black/12 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--muted-foreground)]">Approved</p>
            <p className="mt-3 text-3xl font-semibold text-[color:var(--foreground)]">{summary.approved}</p>
          </div>
          <div className="rounded-2xl border border-white/6 bg-black/12 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--muted-foreground)]">Pending</p>
            <p className="mt-3 text-3xl font-semibold text-[color:var(--foreground)]">{summary.pending}</p>
          </div>
          <div className="rounded-2xl border border-white/6 bg-black/12 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--muted-foreground)]">Skipped</p>
            <p className="mt-3 text-3xl font-semibold text-[color:var(--foreground)]">{summary.skipped}</p>
          </div>
          <div className="rounded-2xl border border-white/6 bg-black/12 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--muted-foreground)]">Uploaded</p>
            <p className="mt-3 text-3xl font-semibold text-[color:var(--foreground)]">{summary.uploaded}</p>
          </div>
        </CardContent>
      </Card>

      <div className="space-y-6">
        {chunks.map((chunk) => (
          <ChunkCard
            chunk={chunk}
            key={chunk.id}
            onChange={updateChunk}
            onStatusChange={(chunkId, status) => updateChunk(chunkId, (current) => ({ ...current, status }))}
          />
        ))}
      </div>
    </div>
  );
}
