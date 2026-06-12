import { AuthForm } from "@/components/auth-form";
import { ApiError, api } from "@/lib/api/client";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

const { pushMock } = vi.hoisted(() => ({ pushMock: vi.fn() }));

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: pushMock }) }));

vi.mock("@marsidev/react-turnstile", () => ({
  Turnstile: ({ onSuccess }: { onSuccess: (t: string) => void }) => (
    <button type="button" onClick={() => onSuccess("test-token")}>
      Complete captcha
    </button>
  ),
}));

vi.mock("@/lib/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api/client")>();
  return { ...actual, api: { login: vi.fn(), register: vi.fn() } };
});

const sampleUser = {
  id: "1",
  email: "a@b.c",
  role: "user",
  is_active: true,
  email_verified: true,
};

afterEach(() => {
  vi.clearAllMocks();
});

describe("AuthForm", () => {
  it("logs in and redirects to the dashboard when email is verified", async () => {
    vi.mocked(api.login).mockResolvedValue(sampleUser);
    const user = userEvent.setup();
    render(<AuthForm mode="login" />);

    await user.type(screen.getByLabelText("E-mail"), "a@b.c");
    await user.type(screen.getByLabelText("Senha"), "secret123");
    await user.click(screen.getByRole("button", { name: "Entrar" }));

    expect(api.login).toHaveBeenCalledWith("a@b.c", "secret123");
    expect(pushMock).toHaveBeenCalledWith("/dashboard");
  });

  it("redirects to /verify-email when email is not verified after login", async () => {
    vi.mocked(api.login).mockResolvedValue({ ...sampleUser, email_verified: false });
    const user = userEvent.setup();
    render(<AuthForm mode="login" />);

    await user.click(screen.getByRole("button", { name: "Entrar" }));

    expect(pushMock).toHaveBeenCalledWith("/verify-email");
  });

  it("registers and redirects to /verify-email", async () => {
    vi.mocked(api.register).mockResolvedValue(sampleUser);
    const user = userEvent.setup();
    render(<AuthForm mode="register" />);

    await user.click(screen.getByRole("button", { name: "Criar conta" }));

    expect(api.register).toHaveBeenCalled();
    expect(pushMock).toHaveBeenCalledWith("/verify-email");
  });

  it("sends the Turnstile token when the widget is enabled", async () => {
    vi.mocked(api.register).mockResolvedValue(sampleUser);
    const user = userEvent.setup();
    render(<AuthForm mode="register" turnstileSiteKey="0x4AAA" />);

    await user.click(screen.getByRole("button", { name: "Complete captcha" }));
    await user.click(screen.getByRole("button", { name: "Criar conta" }));

    expect(api.register).toHaveBeenCalledWith("", "", "test-token");
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
