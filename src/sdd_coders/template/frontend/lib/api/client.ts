/** Thin typed client over the backend API. Cookies carry the session. */

import type { AuditEntry, Project, User, UserUpdate } from "@/lib/api/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    credentials: "include",
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { detail?: unknown };
    const detail = typeof body.detail === "string" ? body.detail : response.statusText;
    throw new ApiError(response.status, detail);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

function jsonBody(value: unknown): RequestInit {
  return { body: JSON.stringify(value) };
}

export const api = {
  register: (email: string, password: string): Promise<User> =>
    request<User>("/auth/register", { method: "POST", ...jsonBody({ email, password }) }),
  login: (email: string, password: string): Promise<User> =>
    request<User>("/auth/login", { method: "POST", ...jsonBody({ email, password }) }),
  logout: (): Promise<void> => request<void>("/auth/logout", { method: "POST" }),
  me: (): Promise<User> => request<User>("/auth/me"),
  listProjects: (): Promise<Project[]> => request<Project[]>("/projects"),
  createProject: (name: string, description: string): Promise<Project> =>
    request<Project>("/projects", { method: "POST", ...jsonBody({ name, description }) }),
  deleteProject: (id: string): Promise<void> =>
    request<void>(`/projects/${id}`, { method: "DELETE" }),
  listUsers: (): Promise<User[]> => request<User[]>("/admin/users"),
  updateUser: (id: string, update: UserUpdate): Promise<User> =>
    request<User>(`/admin/users/${id}`, { method: "PATCH", ...jsonBody(update) }),
  listAudit: (): Promise<AuditEntry[]> => request<AuditEntry[]>("/admin/audit"),
};
