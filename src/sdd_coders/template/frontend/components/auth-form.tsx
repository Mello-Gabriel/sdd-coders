"use client";

import { ApiError, api } from "@/lib/api/client";
import { Turnstile } from "@marsidev/react-turnstile";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

interface AuthFormProps {
  mode: "login" | "register";
  /** When provided, the Turnstile widget is rendered (register mode only). */
  turnstileSiteKey?: string;
}

/** Email + password form used by both the login and register pages. */
export function AuthForm({ mode, turnstileSiteKey }: AuthFormProps) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [turnstileToken, setTurnstileToken] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const showTurnstile = !!turnstileSiteKey && mode === "register";

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      if (mode === "register") {
        await api.register(email, password, turnstileToken);
        router.push("/verify-email");
      } else {
        const user = await api.login(email, password);
        router.push(user.email_verified ? "/dashboard" : "/verify-email");
      }
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Erro inesperado");
    } finally {
      setPending(false);
    }
  };

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-3">
      <label htmlFor="email" className="text-sm font-medium text-foreground">
        E-mail
      </label>
      <input
        id="email"
        type="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        className="rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
      />
      <label htmlFor="password" className="text-sm font-medium text-foreground">
        Senha
      </label>
      <input
        id="password"
        type="password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        className="rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
      />
      {showTurnstile && <Turnstile siteKey={turnstileSiteKey} onSuccess={setTurnstileToken} />}
      {error !== null && <p role="alert">{error}</p>}
      <button
        type="submit"
        disabled={pending}
        className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
      >
        {mode === "register" ? "Criar conta" : "Entrar"}
      </button>
    </form>
  );
}
