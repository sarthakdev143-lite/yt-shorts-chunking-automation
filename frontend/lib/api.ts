import "server-only";

import { appConfig } from "@/lib/config";
import { getMockOverview, getMockPlatformHealth, getMockProject, getMockSettings } from "@/lib/mock-data";
import type { PlatformHealth, Project, ProjectOverview, SettingsSnapshot } from "@/lib/types";

async function fetchBackend<T>(path: string): Promise<T> {
  if (!appConfig.backendBaseUrl) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL is not configured.");
  }

  const response = await fetch(`${appConfig.backendBaseUrl}${path}`, {
    cache: "no-store",
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Backend request failed for ${path}: ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function getDashboardSnapshot(): Promise<ProjectOverview> {
  if (appConfig.demoMode) {
    return getMockOverview();
  }

  return fetchBackend<ProjectOverview>("/api/projects");
}

export async function getProjectSnapshot(projectId: string): Promise<Project | null> {
  if (appConfig.demoMode) {
    return getMockProject(projectId);
  }

  try {
    return await fetchBackend<Project>(`/api/projects/${projectId}`);
  } catch {
    return null;
  }
}

export async function getSettingsSnapshot(): Promise<SettingsSnapshot> {
  if (appConfig.demoMode) {
    return getMockSettings();
  }

  return fetchBackend<SettingsSnapshot>("/health/settings");
}

export async function getPlatformHealth(): Promise<PlatformHealth> {
  if (appConfig.demoMode) {
    return getMockPlatformHealth();
  }

  return fetchBackend<PlatformHealth>("/health");
}
