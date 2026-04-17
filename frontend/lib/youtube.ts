import type { ChunkItem } from "@/lib/types";

export function buildYoutubeUploadPayload(chunk: ChunkItem) {
  return {
    title: chunk.title,
    description: chunk.description,
    tags: chunk.tags,
    privacyStatus: chunk.status === "uploaded" ? "public" : "unlisted",
    thumbnailUrl: chunk.thumbnailUrl,
    videoUrl: chunk.videoUrl,
  };
}

export function getDuplicateGuardLabel(chunk: ChunkItem) {
  if (chunk.duplicateCheck.status === "duplicate") {
    return `Possible duplicate: ${chunk.duplicateCheck.matchedTitle}`;
  }

  if (chunk.duplicateCheck.status === "checking") {
    return "Checking channel inventory before upload";
  }

  return "No duplicate detected";
}
