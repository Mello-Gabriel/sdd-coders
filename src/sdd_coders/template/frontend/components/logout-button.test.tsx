import { LogoutButton } from "@/components/logout-button";
import { api } from "@/lib/api/client";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

const { pushMock } = vi.hoisted(() => ({ pushMock: vi.fn() }));

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: pushMock }) }));
vi.mock("@/lib/api/client", () => ({ api: { logout: vi.fn().mockResolvedValue(undefined) } }));

describe("LogoutButton", () => {
  it("logs out and redirects to login", async () => {
    const user = userEvent.setup();
    render(<LogoutButton />);

    await user.click(screen.getByRole("button", { name: "Sair" }));

    expect(api.logout).toHaveBeenCalled();
    expect(pushMock).toHaveBeenCalledWith("/login");
  });
});
