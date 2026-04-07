const envUrl = import.meta.env.VITE_API_URL;
export const API_URL = (envUrl !== undefined && envUrl !== null) ? envUrl : '';

export async function submitUrls(urls: string[]) {
  const response = await fetch(`${API_URL}/scrape`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ urls })
  });

  if (!response.ok) {
    throw new Error(`Submission failed: ${response.statusText}`);
  }
}

export async function getJobs() {
  const res = await fetch(`${API_URL}/results/all`);
  if (!res.ok) {
    throw new Error(`Failed to fetch jobs`);
  }
  return res.json();
}

export function getDownloadUrl() {
  return `${API_URL}/download`;
}
