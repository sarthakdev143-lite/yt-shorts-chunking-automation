export type PresignedUploadTarget = {
  url: string;
  method: "PUT" | "POST";
  objectKey: string;
  publicUrl?: string;
  fields?: Record<string, string>;
};

export function getTemporaryObjectUrl(baseUrl: string, objectKey: string) {
  return `${baseUrl.replace(/\/$/, "")}/${objectKey}`;
}

export async function uploadFileToPresignedTarget(
  file: File,
  target: PresignedUploadTarget,
  onProgress?: (progress: number) => void,
) {
  if (target.method !== "PUT") {
    throw new Error("This helper currently supports PUT presigned uploads only.");
  }

  await new Promise<void>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("PUT", target.url, true);
    xhr.setRequestHeader("Content-Type", file.type || "application/octet-stream");

    xhr.upload.onprogress = (event) => {
      if (!event.lengthComputable || !onProgress) {
        return;
      }

      onProgress(Math.round((event.loaded / event.total) * 100));
    };

    xhr.onerror = () => reject(new Error("R2 upload failed."));
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve();
        return;
      }

      reject(new Error(`R2 upload failed with status ${xhr.status}.`));
    };

    xhr.send(file);
  });
}
