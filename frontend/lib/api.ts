/**
 * One small wrapper around fetch() used by every page.
 * - the login session lives in an httpOnly cookie set by the backend (JavaScript never sees the token)
 * - every request sends credentials and the CSRF header the backend expects
 * - FastAPI error responses become readable messages
 * - a 401 on a protected call sends the user to the login page
 */

// Empty string = same origin (FastAPI serves the built frontend). In `npm run dev` we call port 8000.
export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? (typeof window !== "undefined" && window.location.port === "3000" ? "http://localhost:8000" : "");

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function readableError(status: number, body: unknown): string {
  const detail = (body as { detail?: unknown })?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length) {
    // Pydantic validation errors: show the first one in plain words
    const first = detail[0] as { loc?: string[]; msg?: string };
    const field = first.loc?.[first.loc.length - 1];
    return `${field ? String(field).replace(/_/g, " ") + ": " : ""}${(first.msg || "Invalid value").replace("Value error, ", "")}`;
  }
  if (status === 429) return "Too many requests. Please wait a moment and try again.";
  if (status >= 500) return "Something went wrong on our side. Please try again.";
  return "Request failed. Please try again.";
}

const PUBLIC_PATHS = ["/", "/login/", "/register/"];

export async function api<T = unknown>(path: string, opts: { method?: string; body?: unknown; form?: FormData } = {}): Promise<T> {
  const headers: Record<string, string> = { "X-Requested-With": "careerpilot" };
  let body: BodyInit | undefined;
  if (opts.form) body = opts.form;
  else if (opts.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(opts.body);
  }
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, { method: opts.method ?? (body ? "POST" : "GET"), headers, body, credentials: "include" });
  } catch {
    throw new ApiError(0, "Cannot reach the CareerPilot server. Check your connection and try again.");
  }
  const data = res.status === 204 ? null : await res.json().catch(() => null);
  if (!res.ok) {
    if (res.status === 401 && typeof window !== "undefined" && !path.startsWith("/api/auth/login") && !path.startsWith("/api/auth/register")) {
      const here = window.location.pathname;
      if (!PUBLIC_PATHS.includes(here)) {
        window.location.href = `/login/?next=${encodeURIComponent(here + window.location.search)}`;
      }
    }
    throw new ApiError(res.status, readableError(res.status, data));
  }
  return data as T;
}

export async function logout(): Promise<void> {
  try {
    await api("/api/auth/logout", { method: "POST" });
  } finally {
    window.location.href = "/login/?signed_out=1";
  }
}
