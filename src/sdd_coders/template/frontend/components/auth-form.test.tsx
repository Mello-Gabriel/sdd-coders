import { AuthForm } from "@/components/auth-form";
import { ApiError, api } from "@/lib/api/client";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

const { pushMock } = vi.hoisted(() => ({ pushMock: vi.fn() }));

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: pushMock }) }));

vi.mock("@/lib/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api/client")>();
  return { ...actual, api: { login: vi.fn(), register: vi.fn() } };
});

const sampleUser = { id: "1", email: "a@b.c", role: "user", is_active: true };

afterEach(() => {
  vi.clearAllMocks();
});

describe("AuthForm", () => {
  it("logs in and redirects to the dashboard", async () => {
    vi.mocked(api.login).mockResolvedValue(sampleUser);
    const user = userEvent.setup();
    render(<AuthForm mode="login" />);

    await user.type(screen.getByLabelText("E-mail"), "a@b.c");
    await user.type(screen.getByLabelText("Senha"), "secret123");
    await user.click(screen.getByRole("button", { name: "Entrar" }));

    expect(api.login).toHaveBeenCalledWith("a@b.c", "secret123");
    expect(pushMock).toHaveBeenCalledWith("/dashboard");
  });

  it("registers and redirects", async () => {
    vi.mocked(api.register).mockResolvedValue(sampleUser);
    const user = userEvent.setup();
    render(<AuthForm mode="register" />);

    await user.click(screen.getByRole("button", { name: "Criar conta" }));

    expect(api.register).toHaveBeenCalled();
    expect(pushMock).toHaveBeenCalledWith("/dashboard");
  });

  it("shows the API error message", async () => {
    vi.mocked(api.login).mockRejectedValue(new ApiError(401, "Credenciais inválidas"));
    const user = userEvent.setup();
    render(<AuthForm mode="login" />);

    await user.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Credenciais inválidas");
  });

  it("shows a generic message for unexpected errors", async () => {
    vi.mocked(api.login).mockRejectedValue(new Error("boom"));
    const user = userEvent.setup();
    render(<AuthForm mode="login" />);

    await user.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Erro inesperado");
  });
});
