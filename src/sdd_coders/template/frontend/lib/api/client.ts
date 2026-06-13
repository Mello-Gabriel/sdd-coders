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
  // Register returns a generic acknowledgement (202), never the user — the
  // endpoint is anti-enumeration, so the response is identical whether or not
  // the email already exists. The user then verifies via the emailed link.
  register: (email: string, password: string, turnstileToken = ""): Promise<void> =>
    request<void>("/auth/register", {
      method: "POST",
      ...jsonBody({ email, password, turnstile_token: turnstileToken }),
    }),
  login: (email: string, password: string): Promise<User> =>
    request<User>("/auth/login", { method: "POST", ...jsonBody({ email, password }) }),
  logout: (): Promise<void> => request<void>("/auth/logout", { method: "POST" }),
  me: (): Promise<User> => request<User>("/auth/me"),
  requestVerification: (email: string): Promise<void> =>
    request<void>("/auth/request-verification", { method: "POST", ...jsonBody({ email }) }),
  verifyEmail: (token: string): Promise<User> =>
    request<User>("/auth/verify-email", { method: "POST", ...jsonBody({ token }) }),
  requestPasswordReset: (email: string, turnstileToken = ""): Promise<void> =>
    request<void>("/auth/request-password-reset", {
      method: "POST",
      ...jsonBody({ email, turnstile_token: turnstileToken }),
    }),
  resetPassword: (token: string, newPassword: string): Promise<User> =>
    request<User>("/auth/reset-password", {
      method: "POST",
      ...jsonBody({ token, new_password: newPassword }),
    }),
  changePassword: (currentPassword: string, newPassword: string): Promise<void> =>
    request<void>("/auth/change-password", {
      method: "POST",
      ...jsonBody({ current_password: currentPassword, new_password: newPassword }),
    }),
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
