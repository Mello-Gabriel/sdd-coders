import { AdminUsers } from "@/components/admin-users";
import { api } from "@/lib/api/client";
import type { User } from "@/lib/api/types";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api/client", () => ({ api: { listUsers: vi.fn(), updateUser: vi.fn() } }));

function user(id: string, email: string, isActive: boolean): User {
  return { id, email, role: "user", is_active: isActive };
}

describe("AdminUsers", () => {
  it("lists users and toggles active state, leaving others untouched", async () => {
    vi.mocked(api.listUsers).mockResolvedValue([
      user("1", "a@b.c", true),
      user("2", "b@b.c", true),
    ]);
    vi.mocked(api.updateUser).mockResolvedValue(user("1", "a@b.c", false));
    const actor = userEvent.setup();
    render(<AdminUsers />);

    expect(await screen.findByText("a@b.c")).toBeInTheDocument();
    expect(screen.getAllByText("ativo")).toHaveLength(2);

    await actor.click(screen.getAllByRole("button", { name: "Desativar" })[0] as HTMLElement);

    expect(await screen.findByText("inativo")).toBeInTheDocument();
    // the other user is unchanged (the map's non-matching branch)
    expect(screen.getByText("inativo")).toBeInTheDocument();
    expect(screen.getAllByText("ativo")).toHaveLength(1);
    expect(api.updateUser).toHaveBeenCalledWith("1", { is_active: false });
  });
});
