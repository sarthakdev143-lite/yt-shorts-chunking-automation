"use client";

import { useMemo, useState } from "react";
import { GripVertical, ListOrdered, Play, RefreshCw, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { ChunkItem, Project } from "@/lib/types";
import { getDuplicateGuardLabel } from "@/lib/youtube";
import { formatDateTime } from "@/lib/utils";

function isoToLocalInput(value: string | null) {
  if (!value) {
    return "";
  }

  const date = new Date(value);
  const offsetMs = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offsetMs).toISOString().slice(0, 16);
}

function localInputToIso(value: string) {
  if (!value) {
    return null;
  }

  return new Date(value).toISOString();
}

export function SchedulerBoard({ project }: { project: Project }) {
  const [chunks, setChunks] = useState([...project.chunks].sort((a, b) => a.order - b.order));
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [intervalHours, setIntervalHours] = useState(project.dailyIntervalHours ?? 24);
  const [queueState, setQueueState] = useState("Queue is ready. Duplicate guard will run before each upload.");

  const uploadQueue = useMemo(
    () =>
      chunks
        .filter((chunk) => chunk.status === "approved" || chunk.status === "uploaded")
        .map((chunk) => ({
          ...chunk,
          queueStatus:
            chunk.status === "uploaded"
              ? "done"
              : chunk.duplicateCheck.status === "duplicate"
                ? "blocked"
                : chunk.scheduledFor
                  ? "queued"
                  : "ready",
        })),
    [chunks],
  );

  function reorder(sourceId: string, targetId: string) {
    setChunks((current) => {
      const next = [...current];
      const sourceIndex = next.findIndex((chunk) => chunk.id === sourceId);
      const targetIndex = next.findIndex((chunk) => chunk.id === targetId);

      if (sourceIndex === -1 || targetIndex === -1) {
        return current;
      }

      const [moved] = next.splice(sourceIndex, 1);
      next.splice(targetIndex, 0, moved);
      return next.map((chunk, index) => ({ ...chunk, order: index + 1 }));
    });
  }

  function updateChunk(chunkId: string, updater: (chunk: ChunkItem) => ChunkItem) {
    setChunks((current) => current.map((chunk) => (chunk.id === chunkId ? updater(chunk) : chunk)));
  }

  function scheduleByInterval() {
    const base = new Date();
    setChunks((current) =>
      current.map((chunk, index) => ({
        ...chunk,
        scheduledFor: chunk.status === "approved" ? new Date(base.getTime() + index * intervalHours * 3600_000).toISOString() : chunk.scheduledFor,
      })),
    );
    setQueueState(`Applied a ${intervalHours}-hour cadence across approved chunks.`);
  }

  function uploadNow() {
    const nextChunk = chunks.find(
      (chunk) => chunk.status === "approved" && chunk.duplicateCheck.status !== "duplicate",
    );

    if (!nextChunk) {
      setQueueState("No approved chunk is ready for upload. Clear duplicate blocks or approve more chunks.");
      return;
    }

    updateChunk(nextChunk.id, (chunk) => ({
      ...chunk,
      status: "uploaded",
      uploadedAt: new Date().toISOString(),
      youtubeVideoId: `yt_${chunk.id}`,
      uploadAttempts: chunk.uploadAttempts + 1,
    }));

    setQueueState(`Uploaded ${nextChunk.title} and marked the processed asset for Drive cleanup.`);
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1.18fr)_minmax(320px,0.82fr)]">
      <div className="space-y-6">
        <Card>
          <CardHeader className="gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[color:var(--accent)]">Upload scheduler</p>
              <CardTitle className="mt-3 text-3xl">Reorder the sequence and release on cadence.</CardTitle>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button onClick={uploadNow} variant="primary">
                <Play className="mr-2 h-4 w-4" />
                Upload now
              </Button>
              <Button onClick={scheduleByInterval} variant="secondary">
                <RefreshCw className="mr-2 h-4 w-4" />
                Apply interval
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {chunks.map((chunk) => (
              <div
                className="rounded-[28px] border border-white/6 bg-black/12 p-4"
                draggable
                key={chunk.id}
                onDragEnd={() => setDraggingId(null)}
                onDragOver={(event) => event.preventDefault()}
                onDragStart={() => setDraggingId(chunk.id)}
                onDrop={() => {
                  if (draggingId && draggingId !== chunk.id) {
                    reorder(draggingId, chunk.id);
                  }
                }}
              >
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div className="flex min-w-0 flex-1 gap-4">
                    <div className="rounded-2xl border border-white/8 bg-black/18 p-3 text-[color:var(--muted-foreground)]">
                      <GripVertical className="h-5 w-5" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--muted-foreground)]">
                        Order {chunk.order}
                      </p>
                      <h3 className="mt-2 truncate text-xl font-semibold text-[color:var(--foreground)]">{chunk.title}</h3>
                      <p className="mt-2 text-sm leading-6 text-[color:var(--muted-foreground)]">{getDuplicateGuardLabel(chunk)}</p>
                    </div>
                  </div>
                  <Badge variant={chunk.status === "uploaded" ? "accent" : chunk.status === "approved" ? "success" : "warning"}>
                    {chunk.status}
                  </Badge>
                </div>

                <div className="mt-4 grid gap-3 lg:grid-cols-[1fr_260px]">
                  <div className="rounded-2xl border border-white/6 bg-black/14 p-4 text-sm text-[color:var(--muted-foreground)]">
                    <div className="flex items-center gap-2 font-semibold uppercase tracking-[0.22em] text-[color:var(--foreground)]">
                      <ShieldCheck className="h-4 w-4 text-[color:var(--accent)]" />
                      Duplicate guard
                    </div>
                    <p className="mt-3 leading-6">{getDuplicateGuardLabel(chunk)}</p>
                  </div>
                  <div>
                    <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--muted-foreground)]">
                      Schedule slot
                    </label>
                    <Input
                      onChange={(event) =>
                        updateChunk(chunk.id, (current) => ({
                          ...current,
                          scheduledFor: localInputToIso(event.target.value),
                        }))
                      }
                      type="datetime-local"
                      value={isoToLocalInput(chunk.scheduledFor)}
                    />
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="space-y-6">
        <Card>
          <CardHeader>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--accent)]">Cadence</p>
            <CardTitle className="mt-3 text-2xl">Daily interval scheduling</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input onChange={(event) => setIntervalHours(Number(event.target.value) || intervalHours)} type="number" value={intervalHours} />
            <p className="text-sm leading-6 text-[color:var(--muted-foreground)]">{queueState}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--accent)]">
              <ListOrdered className="h-4 w-4" />
              Live queue
            </div>
            <CardTitle className="mt-3 text-2xl">Queued to upload</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {uploadQueue.map((chunk) => (
              <div className="rounded-2xl border border-white/6 bg-black/12 p-4" key={chunk.id}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-medium text-[color:var(--foreground)]">{chunk.title}</p>
                    <p className="mt-2 text-sm leading-6 text-[color:var(--muted-foreground)]">{formatDateTime(chunk.scheduledFor)}</p>
                  </div>
                  <Badge
                    variant={
                      chunk.queueStatus === "done"
                        ? "accent"
                        : chunk.queueStatus === "blocked"
                          ? "danger"
                          : chunk.queueStatus === "queued"
                            ? "success"
                            : "warning"
                    }
                  >
                    {chunk.queueStatus}
                  </Badge>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
