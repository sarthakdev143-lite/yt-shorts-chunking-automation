export const backendBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? null;
export const demoMode = process.env.NEXT_PUBLIC_DEMO_MODE !== "false" || !backendBaseUrl;

export const appConfig = {
  name: "Shortsmith",
  description: "Chunk long-form footage into reviewable Shorts-ready assets with temporary Google Drive storage and YouTube scheduling.",
  backendBaseUrl,
  demoMode,
  wakingThresholdMs: 1400,
};
