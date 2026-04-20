export async function uploadFileToBackend(
  file: File,
  endpoint: string,
  fields: Record<string, string>,
  onProgress?: (progress: number) => void,
) {
  const formData = new FormData();
  formData.append("file", file);
  Object.entries(fields).forEach(([key, value]) => {
    formData.append(key, value);
  });

  await new Promise<void>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", endpoint, true);

    xhr.upload.onprogress = (event) => {
      if (!event.lengthComputable || !onProgress) {
        return;
      }
      onProgress(Math.round((event.loaded / event.total) * 100));
    };

    xhr.onerror = () => reject(new Error("Backend upload failed."));
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve();
        return;
      }
      reject(new Error(`Backend upload failed with status ${xhr.status}.`));
    };

    xhr.send(formData);
  });
}
