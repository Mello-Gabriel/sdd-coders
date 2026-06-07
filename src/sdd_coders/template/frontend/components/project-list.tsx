"use client";

import { ApiError, api } from "@/lib/api/client";
import type { Project } from "@/lib/api/types";
import { type FormEvent, useEffect, useState } from "react";

export function ProjectList() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .listProjects()
      .then(setProjects)
      .catch((caught: unknown) => {
        setError(caught instanceof ApiError ? caught.message : "Erro ao carregar");
      })
      .finally(() => setLoading(false));
  }, []);

  const create = async (event: FormEvent) => {
    event.preventDefault();
    const created = await api.createProject(name, "");
    setProjects((current) => [...current, created]);
    setName("");
  };

  const remove = async (id: string) => {
    await api.deleteProject(id);
    setProjects((current) => current.filter((project) => project.id !== id));
  };

  if (loading) {
    return <p>Carregando…</p>;
  }

  return (
    <section>
      {error !== null && <p role="alert">{error}</p>}
      <ul>
        {projects.map((project) => (
          <li key={project.id}>
            {project.name}
            <button type="button" onClick={() => remove(project.id)}>
              Excluir
            </button>
          </li>
        ))}
      </ul>
      <form onSubmit={create}>
        <label htmlFor="project-name">Novo projeto</label>
        <input id="project-name" value={name} onChange={(event) => setName(event.target.value)} />
        <button type="submit">Criar</button>
      </form>
    </section>
  );
}
