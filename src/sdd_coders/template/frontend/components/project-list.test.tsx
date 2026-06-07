import { ProjectList } from "@/components/project-list";
import { ApiError, api } from "@/lib/api/client";
import type { Project } from "@/lib/api/types";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api/client")>();
  return {
    ...actual,
    api: { listProjects: vi.fn(), createProject: vi.fn(), deleteProject: vi.fn() },
  };
});

function project(id: string, name: string): Project {
  return { id, name, owner_id: "o", description: "", created_at: "", updated_at: "" };
}

afterEach(() => {
  vi.clearAllMocks();
});

describe("ProjectList", () => {
  it("renders the loaded projects", async () => {
    vi.mocked(api.listProjects).mockResolvedValue([project("1", "Alpha")]);
    render(<ProjectList />);
    expect(await screen.findByText("Alpha")).toBeInTheDocument();
  });

  it("shows the API error when loading fails", async () => {
    vi.mocked(api.listProjects).mockRejectedValue(new ApiError(500, "Falhou"));
    render(<ProjectList />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Falhou");
  });

  it("shows a generic error on unexpected load failure", async () => {
    vi.mocked(api.listProjects).mockRejectedValue(new Error("x"));
    render(<ProjectList />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Erro ao carregar");
  });

  it("creates a project", async () => {
    vi.mocked(api.listProjects).mockResolvedValue([]);
    vi.mocked(api.createProject).mockResolvedValue(project("2", "Beta"));
    const user = userEvent.setup();
    render(<ProjectList />);
    await screen.findByRole("button", { name: "Criar" });

    await user.type(screen.getByLabelText("Novo projeto"), "Beta");
    await user.click(screen.getByRole("button", { name: "Criar" }));

    expect(await screen.findByText("Beta")).toBeInTheDocument();
    expect(api.createProject).toHaveBeenCalledWith("Beta", "");
  });

  it("deletes a project", async () => {
    vi.mocked(api.listProjects).mockResolvedValue([project("1", "Alpha")]);
    vi.mocked(api.deleteProject).mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<ProjectList />);
    await screen.findByText("Alpha");

    await user.click(screen.getByRole("button", { name: "Excluir" }));

    await waitFor(() => {
      expect(screen.queryByText("Alpha")).toBeNull();
    });
  });
});
