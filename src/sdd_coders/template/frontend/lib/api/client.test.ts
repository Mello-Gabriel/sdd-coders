import { ApiError, api } from "@/lib/api/client";
import { afterEach, describe, expect, it, vi } from "vitest";

function ok(body: unknown, status = 200): Response {
  return { ok: true, status, json: () => Promise.resolve(body) } as unknown as Response;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("api client", () => {
  it("returns the parsed body on success", async () => {
    const user = { id: "1", email: "a@b.c", role: "user", is_active: true };
    const fetchMock = vi.fn().mockResolvedValue(ok(user));
    vi.stubGlobal("fetch", fetchMock);

    await expect(api.me()).resolves.toEqual(user);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/auth/me",
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("returns undefined for 204 responses", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, status: 204 } as Response));
    await expect(api.logout()).resolves.toBeUndefined();
  });

  it("throws ApiError carrying the server detail", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        statusText: "Unauthorized",
        json: () => Promise.resolve({ detail: "Invalid credentials" }),
      } as unknown as Response),
    );

    const error = await api.login("a@b.c", "pw").catch((value: unknown) => value);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBe(401);
    expect((error as ApiError).message).toBe("Invalid credentials");
  });

  it("falls back to statusText when the error has no detail", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        statusText: "Server Error",
        json: () => Promise.reject(new Error("no body")),
      } as unknown as Response),
    );

    const error = await api.me().catch((value: unknown) => value);
    expect((error as ApiError).message).toBe("Server Error");
  });

  it("uses the right method and path for each endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue(ok({}));
    vi.stubGlobal("fetch", fetchMock);

    await api.register("a@b.c", "pw");
    await api.createProject("P", "d");
    await api.deleteProject("p1");
    await api.listProjects();
    await api.listUsers();
    await api.updateUser("u1", { is_active: false });
    await api.listAudit();

    const calls = fetchMock.mock.calls.map(
      (call) => `${(call[1] as RequestInit).method ?? "GET"} ${call[0]}`,
    );
    expect(calls).toEqual([
      "POST http://localhost:8000/auth/register",
      "POST http://localhost:8000/projects",
      "DELETE http://localhost:8000/projects/p1",
      "GET http://localhost:8000/projects",
      "GET http://localhost:8000/admin/users",
      "PATCH http://localhost:8000/admin/users/u1",
      "GET http://localhost:8000/admin/audit",
    ]);
  });
});
