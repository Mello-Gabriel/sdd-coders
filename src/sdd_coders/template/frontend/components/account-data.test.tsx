import { AccountData } from "@/components/account-data";
import { api } from "@/lib/api/client";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const pushMock = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push: pushMock }) }));
vi.mock("@/lib/api/client", () => ({
  api: { exportData: vi.fn(), deleteAccount: vi.fn() },
}));

beforeEach(() => {
  vi.stubGlobal("URL", {
    createObjectURL: vi.fn(() => "blob:fake"),
    revokeObjectURL: vi.fn(),
  });
  // jsdom doesn't implement anchor downloads; stub the click.
  vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
});

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe("AccountData", () => {
  it("exports data as a JSON download", async () => {
    vi.mocked(api.exportData).mockResolvedValue({
      user: { id: "1", email: "a@b.c", role: "user", is_active: true, email_verified: true },
      projects: [],
      consents: [],
      audit: [],
    });
    const user = userEvent.setup();
    render(<AccountData />);

    await user.click(screen.getByRole("button", { name: "Exportar meus dados" }));

    expect(api.exportData).toHaveBeenCalled();
  });

  it("shows an error when export fails", async () => {
    vi.mocked(api.exportData).mockRejectedValue(new Error("boom"));
    const user = userEvent.setup();
    render(<AccountData />);

    await user.click(screen.getByRole("button", { name: "Exportar meus dados" }));

    expect(screen.getByRole("status")).toHaveTextContent("Não foi possível exportar");
  });

  it("requires confirmation before deleting", async () => {
    const user = userEvent.setup();
    render(<AccountData />);

    await user.click(screen.getByRole("button", { name: "Excluir minha conta" }));
    expect(screen.getByRole("button", { name: "Confirmar exclusão" })).toBeInTheDocument();
  });

  it("cancels the deletion confirmation", async () => {
    const user = userEvent.setup();
    render(<AccountData />);

    await user.click(screen.getByRole("button", { name: "Excluir minha conta" }));
    await user.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(screen.queryByRole("button", { name: "Confirmar exclusão" })).toBeNull();
  });

  it("deletes the account and redirects to login", async () => {
    vi.mocked(api.deleteAccount).mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<AccountData />);

    await user.click(screen.getByRole("button", { name: "Excluir minha conta" }));
    await user.click(screen.getByRole("button", { name: "Confirmar exclusão" }));

    expect(api.deleteAccount).toHaveBeenCalled();
    expect(pushMock).toHaveBeenCalledWith("/login");
  });

  it("shows an error when deletion fails", async () => {
    vi.mocked(api.deleteAccount).mockRejectedValue(new Error("boom"));
    const user = userEvent.setup();
    render(<AccountData />);

    await user.click(screen.getByRole("button", { name: "Excluir minha conta" }));
    await user.click(screen.getByRole("button", { name: "Confirmar exclusão" }));

    expect(screen.getByRole("status")).toHaveTextContent("Não foi possível excluir");
  });
});
