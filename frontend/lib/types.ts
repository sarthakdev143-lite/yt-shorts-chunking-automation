import { z } from "zod";

export const subtitleCueSchema = z.object({
  id: z.string(),
  startSeconds: z.number(),
  endSeconds: z.number(),
  text: z.string(),
});

export const duplicateCheckSchema = z.object({
  status: z.enum(["clear", "duplicate", "checking"]),
  matchedTitle: z.string().nullable(),
});

export const chunkSchema = z.object({
  id: z.string(),
  projectId: z.string(),
  order: z.number(),
  title: z.string(),
  description: z.string(),
  tags: z.array(z.string()),
  status: z.enum(["pending", "approved", "skipped", "uploaded"]),
  durationSeconds: z.number(),
  sourceRange: z.object({
    startSeconds: z.number(),
    endSeconds: z.number(),
  }),
  trimRange: z.object({
    startSeconds: z.number(),
    endSeconds: z.number(),
  }),
  reframe: z.object({
    zoom: z.number(),
    blur: z.number(),
  }),
  videoUrl: z.string(),
  thumbnailUrl: z.string(),
  r2VideoUrl: z.string(),
  r2ThumbnailUrl: z.string(),
  scheduledFor: z.string().nullable(),
  uploadedAt: z.string().nullable(),
  youtubeVideoId: z.string().nullable(),
  uploadAttempts: z.number(),
  duplicateCheck: duplicateCheckSchema,
  lastError: z.string().nullable(),
  subtitleCues: z.array(subtitleCueSchema),
});

export const projectSchema = z.object({
  id: z.string(),
  name: z.string(),
  status: z.enum(["processing", "ready", "scheduled", "complete", "failed"]),
  privacy: z.enum(["private", "unlisted", "public"]),
  chunkDuration: z.number(),
  sceneDetection: z.boolean(),
  sourceVideoKey: z.string(),
  sourceVideoUrl: z.string(),
  createdAt: z.string(),
  updatedAt: z.string(),
  uploadProgress: z.number(),
  processingStage: z.string(),
  queueDepth: z.number(),
  channelName: z.string(),
  scheduleMode: z.enum(["manual", "interval"]),
  dailyIntervalHours: z.number().nullable(),
  descriptionTemplate: z.string(),
  chunks: z.array(chunkSchema),
});

export const activityItemSchema = z.object({
  id: z.string(),
  timestamp: z.string(),
  label: z.string(),
  kind: z.enum(["processing", "upload", "storage"]),
});

export const demoSeedSchema = z.object({
  projects: z.array(projectSchema),
  activity: z.array(activityItemSchema),
});

export type SubtitleCue = z.infer<typeof subtitleCueSchema>;
export type ChunkItem = z.infer<typeof chunkSchema>;
export type Project = z.infer<typeof projectSchema>;
export type ActivityItem = z.infer<typeof activityItemSchema>;
export type DemoSeed = z.infer<typeof demoSeedSchema>;

export type DashboardSummary = {
  totalProjects: number;
  approvedChunks: number;
  pendingChunks: number;
  uploadedChunks: number;
  activeProcessingJobs: number;
};

export type ProjectOverview = {
  projects: Project[];
  activity: ActivityItem[];
  summary: DashboardSummary;
};

export type ServiceHealth = {
  name: string;
  status: "ready" | "degraded" | "demo";
  detail: string;
};

export type PlatformHealth = {
  mode: "demo" | "live";
  backendUrl: string | null;
  services: ServiceHealth[];
};

export type SettingsSnapshot = {
  auth: {
    googleConfigured: boolean;
    nextAuthSecretConfigured: boolean;
    youtubeScope: string;
  };
  storage: {
    driveConfigured: boolean;
    folderId: string | null;
    tempRetentionRule: string;
  };
  processing: {
    groqConfigured: boolean;
    chunkConcurrency: number;
    ffmpegStrategy: string;
  };
  data: {
    supabaseConfigured: boolean;
    redisConfigured: boolean;
  };
};
