"use client";

import { ApiError, api } from "@/lib/api/client";
import { type FormEvent, useState } from "react";

export function ChangePasswordForm() {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [pending, setPending] = useState(false);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (next !== confirm) {
      setError("As senhas não coincidem");
      return;
    }
    setPending(true);
    setError(null);
    try {
      await api.changePassword(current, next);
      setSuccess(true);
      setCurrent("");
      setNext("");
      setConfirm("");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Erro inesperado");
    } finally {
      setPending(false);
    }
  };

  if (success) {
    return <output>Senha alterada com sucesso.</output>;
  }

  return (
    <form onSubmit={onSubmit}>
      <label htmlFor="current-password">Senha atual</label>
      <input
        id="current-password"
        type="password"
        value={current}
        onChange={(e) => setCurrent(e.target.value)}
        className="block w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
      />
      <label htmlFor="new-password">Nova senha</label>
      <input
        id="new-password"
        type="password"
        value={next}
        onChange={(e) => setNext(e.target.value)}
        className="block w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
      />
      <label htmlFor="confirm-password">Confirmar nova senha</label>
      <input
        id="confirm-password"
        type="password"
        value={confirm}
        onChange={(e) => setConfirm(e.target.value)}
        className="block w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
      />
      {error !== null && <p role="alert">{error}</p>}
      <button
        type="submit"
        disabled={pending}
        className="mt-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
      >
        Alterar senha
      </button>
    </form>
  );
}
