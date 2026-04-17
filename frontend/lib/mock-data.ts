import seedData from "@/data/demo-projects.json";
import { appConfig } from "@/lib/config";
import type {
  ActivityItem,
  DashboardSummary,
  DemoSeed,
  PlatformHealth,
  Project,
  ProjectOverview,
  SettingsSnapshot,
} from "@/lib/types";
import { demoSeedSchema } from "@/lib/types";

const parsedSeed = demoSeedSchema.parse(seedData) as DemoSeed;

export const mockProjects = parsedSeed.projects satisfies Project[];
export const mockActivity = parsedSeed.activity satisfies ActivityItem[];

export function getMockProject(projectId: string) {
  return mockProjects.find((project) => project.id === projectId) ?? null;
}

export function getMockSummary(): DashboardSummary {
  const chunks = mockProjects.flatMap((project) => project.chunks);

  return {
    totalProjects: mockProjects.length,
    approvedChunks: chunks.filter((chunk) => chunk.status === "approved").length,
    pendingChunks: chunks.filter((chunk) => chunk.status === "pending").length,
    uploadedChunks: chunks.filter((chunk) => chunk.status === "uploaded").length,
    activeProcessingJobs: mockProjects.filter((project) => project.status === "processing").length,
  };
}

export function getMockOverview(): ProjectOverview {
  return {
    projects: mockProjects,
    activity: mockActivity,
    summary: getMockSummary(),
  };
}

export function getMockPlatformHealth(): PlatformHealth {
  return {
    mode: appConfig.demoMode ? "demo" : "live",
    backendUrl: appConfig.backendBaseUrl,
    services: [
      {
        name: "Render API",
        status: appConfig.demoMode ? "demo" : "ready",
        detail: appConfig.demoMode
          ? "Running in seeded demo mode until NEXT_PUBLIC_API_BASE_URL is set."
          : "Backend configured via NEXT_PUBLIC_API_BASE_URL.",
      },
      {
        name: "Cloudflare R2",
        status: process.env.CLOUDFLARE_R2_BUCKET_NAME ? "ready" : "demo",
        detail: process.env.CLOUDFLARE_R2_BUCKET_NAME
          ? `Temporary transit bucket: ${process.env.CLOUDFLARE_R2_BUCKET_NAME}`
          : "Presigned upload flow is scaffolded; bucket env vars are missing.",
      },
      {
        name: "Upstash Redis",
        status: process.env.UPSTASH_REDIS_URL ? "ready" : "demo",
        detail: process.env.UPSTASH_REDIS_URL
          ? "Celery broker configured."
          : "Worker queue is wired for Redis, currently mocked in UI.",
      },
      {
        name: "Supabase",
        status: process.env.SUPABASE_URL ? "ready" : "demo",
        detail: process.env.SUPABASE_URL
          ? "Project metadata can persist to Postgres-compatible Supabase."
          : "Project metadata is served from the bundled demo seed.",
      },
      {
        name: "YouTube OAuth",
        status: process.env.GOOGLE_CLIENT_ID ? "ready" : "demo",
        detail: process.env.GOOGLE_CLIENT_ID
          ? "Google OAuth scope includes youtube.upload."
          : "Google OAuth wiring is present but credentials are not configured.",
      },
    ],
  };
}

export function getMockSettings(): SettingsSnapshot {
  return {
    auth: {
      googleConfigured: Boolean(process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET),
      nextAuthSecretConfigured: Boolean(process.env.NEXTAUTH_SECRET),
      youtubeScope: "openid email profile https://www.googleapis.com/auth/youtube.upload",
    },
    storage: {
      r2Configured: Boolean(
        process.env.CLOUDFLARE_R2_ACCESS_KEY &&
          process.env.CLOUDFLARE_R2_SECRET_KEY &&
          process.env.CLOUDFLARE_R2_BUCKET_NAME &&
          process.env.CLOUDFLARE_R2_ENDPOINT,
      ),
      bucketName: process.env.CLOUDFLARE_R2_BUCKET_NAME ?? null,
      tempRetentionRule: "Delete raw chunk after processing, then delete processed Short after successful YouTube upload.",
    },
    processing: {
      groqConfigured: Boolean(process.env.GROQ_API_KEY),
      chunkConcurrency: 1,
      ffmpegStrategy: "Scene-aware or fixed splits processed serially to stay under Render free-tier memory limits.",
    },
    data: {
      supabaseConfigured: Boolean(process.env.SUPABASE_URL && process.env.SUPABASE_ANON_KEY),
      redisConfigured: Boolean(process.env.UPSTASH_REDIS_URL),
    },
  };
}
