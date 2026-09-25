export class ApiError extends Error {
  readonly status: number;
  readonly code?: string;
  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

type RequestOptions = RequestInit & { timeoutMs?: number; retries?: number };

export async function requestJson<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { timeoutMs = 15000, retries = options.method && options.method !== "GET" ? 0 : 1, ...init } = options;
  let lastError: unknown;
  for (let attempt = 0; attempt <= retries; attempt += 1) {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(path, {
        credentials: "same-origin",
        ...init,
        signal: controller.signal,
        headers: { Accept: "application/json", ...(init.body ? { "Content-Type": "application/json" } : {}), ...init.headers },
      });
      const payload = await response.json().catch(() => null);
      if (!response.ok) {
        const detail = payload?.detail;
        throw new ApiError(detail?.message ?? `${response.status} ${response.statusText}`, response.status, detail?.code);
      }
      return payload as T;
    } catch (error) {
      lastError = error;
      if (error instanceof ApiError || attempt === retries) throw error;
      await new Promise((resolve) => window.setTimeout(resolve, 150 * (attempt + 1)));
    } finally {
      window.clearTimeout(timer);
    }
  }
  throw lastError instanceof Error ? lastError : new Error("Request failed");
}
