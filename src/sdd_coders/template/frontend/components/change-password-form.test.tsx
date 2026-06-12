import { ChangePasswordForm } from "@/components/change-password-form";
import { ApiError, api } from "@/lib/api/client";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api/client")>();
  return { ...actual, api: { changePassword: vi.fn() } };
});

afterEach(() => {
  vi.clearAllMocks();
});

async function fillAndSubmit(
  current: string,
  next: string,
  confirm: string,
  user: ReturnType<typeof userEvent.setup>,
) {
  await user.type(screen.getByLabelText("Senha atual"), current);
  await user.type(screen.getByLabelText("Nova senha"), next);
  await user.type(screen.getByLabelText("Confirmar nova senha"), confirm);
  await user.click(screen.getByRole("button", { name: "Alterar senha" }));
}

describe("ChangePasswordForm", () => {
  it("shows an error when new passwords do not match", async () => {
    const user = userEvent.setup();
    render(<ChangePasswordForm />);

    await fillAndSubmit("old", "new1", "new2", user);

    expect(screen.getByRole("alert")).toHaveTextContent("As senhas não coincidem");
    expect(api.changePassword).not.toHaveBeenCalled();
  });

  it("shows success message after a successful password change", async () => {
    vi.mocked(api.changePassword).mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<ChangePasswordForm />);

    await fillAndSubmit("old", "new1", "new1", user);

    expect(await screen.findByRole("status")).toHaveTextContent("Senha alterada com sucesso.");
  });

  it("shows the API error message on failure", async () => {
    vi.mocked(api.changePassword).mockRejectedValue(new ApiError(400, "Senha atual incorreta"));
    const user = userEvent.setup();
    render(<ChangePasswordForm />);

    await fillAndSubmit("wrong", "new1", "new1", user);

    expect(await screen.findByRole("alert")).toHaveTextContent("Senha atual incorreta");
  });

  it("shows a generic error for unexpected failures", async () => {
    vi.mocked(api.changePassword).mockRejectedValue(new Error("boom"));
    const user = userEvent.setup();
    render(<ChangePasswordForm />);

    await fillAndSubmit("old", "new1", "new1", user);

    expect(await screen.findByRole("alert")).toHaveTextContent("Erro inesperado");
  });
});
