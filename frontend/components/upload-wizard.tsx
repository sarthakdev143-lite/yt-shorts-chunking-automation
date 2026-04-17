"use client";

import { useMemo, useState } from "react";
import { CheckCircle2, Video } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Switch } from "@/components/ui/switch";
import { appConfig } from "@/lib/config";
import { uploadFileToPresignedTarget } from "@/lib/r2";

const defaultPrivacy = ["private", "unlisted", "public"] as const;

type UploadState = {
  projectName: string;
  chunkDuration: number;
  sceneDetection: boolean;
  privacy: (typeof defaultPrivacy)[number];
};

export function UploadWizard() {
  const [file, setFile] = useState<File | null>(null);
  const [form, setForm] = useState<UploadState>({
    projectName: "",
    chunkDuration: 45,
    sceneDetection: true,
    privacy: "unlisted",
  });
  const [uploadProgress, setUploadProgress] = useState(0);
  const [status, setStatus] = useState("Ready for a user-owned or licensed source video.");
  const [submitting, setSubmitting] = useState(false);

  const canSubmit = useMemo(() => Boolean(file && form.projectName.trim()), [file, form.projectName]);

  async function handleSubmit() {
    if (!file || !canSubmit) {
      return;
    }

    setSubmitting(true);
    setUploadProgress(0);

    try {
      if (appConfig.demoMode || !appConfig.backendBaseUrl) {
        setStatus("Demo mode: simulating presigned R2 upload and Celery job dispatch.");

        for (const progress of [12, 27, 41, 55, 72, 89, 100]) {
          await new Promise((resolve) => setTimeout(resolve, 180));
          setUploadProgress(progress);
        }

        setStatus("Demo upload completed. Celery pipeline would start processing immediately.");
      } else {
        setStatus("Requesting presigned upload target from backend...");

        const targetResponse = await fetch(`${appConfig.backendBaseUrl}/api/upload/presign`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            filename: file.name,
            contentType: file.type,
            projectName: form.projectName,
            chunkDuration: form.chunkDuration,
            sceneDetection: form.sceneDetection,
            privacy: form.privacy,
          }),
        });

        if (!targetResponse.ok) {
          throw new Error(`Presign failed: ${targetResponse.status}`);
        }

        const target = (await targetResponse.json()) as {
          url: string;
          method: "PUT";
          objectKey: string;
        };

        setStatus("Uploading directly to Cloudflare R2...");
        await uploadFileToPresignedTarget(file, target, setUploadProgress);

        setStatus("Notifying backend to enqueue Celery processing task...");
        await fetch(`${appConfig.backendBaseUrl}/api/upload/complete`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            objectKey: target.objectKey,
            projectName: form.projectName,
            chunkDuration: form.chunkDuration,
            sceneDetection: form.sceneDetection,
            privacy: form.privacy,
          }),
        });

        setStatus("Upload complete. Project has been queued for background processing.");
      }
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Upload failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Card className="overflow-hidden">
      <CardHeader className="gap-4 border-b border-white/6 pb-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[color:var(--accent)]">Upload & queue</p>
            <CardTitle className="mt-3 text-3xl">Direct-to-R2 ingest with no backend file buffering.</CardTitle>
          </div>
          <div className="rounded-full border border-[color:var(--line)] bg-white/5 px-4 py-2 text-xs uppercase tracking-[0.2em] text-[color:var(--muted-foreground)]">
            Render-safe memory profile
          </div>
        </div>
        <CardDescription>
          Raw footage is uploaded to temporary R2 storage, chunked one segment at a time, then deleted as soon as the processed Short is safely persisted or uploaded.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-6 py-6 lg:grid-cols-[1.15fr_0.85fr]">
        <div className="space-y-4">
          <label className="block rounded-[28px] border border-dashed border-[color:var(--line)] bg-black/12 p-6 text-sm text-[color:var(--muted-foreground)] transition hover:border-[color:var(--accent)]/40 hover:bg-black/16">
            <span className="mb-4 flex items-center gap-3 text-[color:var(--foreground)]">
              <Video className="h-5 w-5 text-[color:var(--accent)]" />
              {file ? file.name : "Drop a long-form source file or browse"}
            </span>
            <span className="block leading-6">
              Accepts user-owned or licensed source footage only. The backend never proxies the file payload; it only receives metadata and queue commands.
            </span>
            <input
              accept="video/*"
              className="sr-only"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              type="file"
            />
          </label>

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--muted-foreground)]">
                Project name
              </label>
              <Input
                onChange={(event) => setForm((current) => ({ ...current, projectName: event.target.value }))}
                placeholder="April founder story"
                value={form.projectName}
              />
            </div>
            <div>
              <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--muted-foreground)]">
                Chunk duration (seconds)
              </label>
              <Input
                min={15}
                onChange={(event) =>
                  setForm((current) => ({ ...current, chunkDuration: Number(event.target.value) || current.chunkDuration }))
                }
                type="number"
                value={form.chunkDuration}
              />
            </div>
          </div>
        </div>

        <div className="space-y-5 rounded-[28px] border border-white/6 bg-black/12 p-5">
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--muted-foreground)]">Defaults</p>
            <div className="flex items-center justify-between rounded-2xl border border-white/6 bg-black/14 px-4 py-3">
              <div>
                <p className="font-medium text-[color:var(--foreground)]">Scene detection</p>
                <p className="text-sm text-[color:var(--muted-foreground)]">Use FFmpeg scene-aware split points when possible.</p>
              </div>
              <Switch
                checked={form.sceneDetection}
                onChange={(checked) => setForm((current) => ({ ...current, sceneDetection: checked }))}
              />
            </div>
            <div>
              <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--muted-foreground)]">
                Privacy status
              </label>
              <div className="grid grid-cols-3 gap-2">
                {defaultPrivacy.map((privacy) => (
                  <button
                    className={`rounded-2xl border px-3 py-3 text-sm capitalize transition ${
                      form.privacy === privacy
                        ? "border-[color:var(--accent)] bg-[color:var(--accent)]/12 text-[color:var(--foreground)]"
                        : "border-[color:var(--line)] bg-white/4 text-[color:var(--muted-foreground)] hover:bg-white/8"
                    }`}
                    key={privacy}
                    onClick={() => setForm((current) => ({ ...current, privacy }))}
                    type="button"
                  >
                    {privacy}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm text-[color:var(--muted-foreground)]">
              <span>Upload progress</span>
              <span>{uploadProgress}%</span>
            </div>
            <Progress value={uploadProgress} />
            <p className="text-sm leading-6 text-[color:var(--muted-foreground)]">{status}</p>
          </div>

          <Button className="w-full" disabled={!canSubmit || submitting} onClick={handleSubmit}>
            {submitting ? "Uploading..." : "Upload and trigger processing"}
          </Button>
          <div className="flex items-start gap-3 rounded-2xl border border-emerald-400/12 bg-emerald-400/8 px-4 py-3 text-sm text-emerald-100">
            <CheckCircle2 className="mt-0.5 h-4 w-4 text-emerald-300" />
            Final processed Shorts are also treated as temporary transit assets and deleted from R2 after successful YouTube upload.
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
