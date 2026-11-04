export type DocumentRecord = { id: string; name: string; byte_size: number; chunk_count: number; created_at: string };
export type Citation = { id: number; name: string; page: number; ordinal: number; quote: string; passage: string };
export type Answer = { id: string; question: string; answer: string; citations: Citation[]; grounded: boolean; created_at: string };
export type Workspace = { documents: DocumentRecord[]; expires_at: string; ai_ready: boolean; provider: string; model: string; limits: { file_bytes: number; documents: number; questions_per_day: number } };

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) { super(message); this.status = status; }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api/${path}`, { ...options, cache: "no-store", credentials: "same-origin" });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = typeof data?.detail === "string" ? data.detail : response.status === 422 ? "Please check your file or question and try again." : "The request could not be completed. Please retry.";
    throw new ApiError(detail, response.status);
  }
  return data as T;
}
