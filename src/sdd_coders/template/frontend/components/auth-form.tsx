"use client";

import { ApiError, api } from "@/lib/api/client";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

interface AuthFormProps {
  mode: "login" | "register";
}

/** Email + password form used by both the login and register pages. */
export function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      if (mode === "register") {
        await api.register(email, password);
      } else {
        await api.login(email, password);
      }
      router.push("/dashboard");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Erro inesperado");
    } finally {
      setPending(false);
    }
  };

  return (
    <form onSubmit={onSubmit}>
      <label htmlFor="email">E-mail</label>
      <input
        id="email"
        type="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
      />
      <label htmlFor="password">Senha</label>
      <input
        id="password"
        type="password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
      />
      {error !== null && <p role="alert">{error}</p>}
      <button type="submit" disabled={pending}>
        {mode === "register" ? "Criar conta" : "Entrar"}
      </button>
    </form>
  );
}
