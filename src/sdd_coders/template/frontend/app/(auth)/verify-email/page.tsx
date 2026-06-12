"use client";

import { ApiError, api } from "@/lib/api/client";
import { useSearchParams } from "next/navigation";
import { type FormEvent, Suspense, useEffect, useState } from "react";

type Status = "pending" | "verifying" | "success" | "error";

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [status, setStatus] = useState<Status>(token ? "verifying" : "pending");
  const [email, setEmail] = useState("");
  const [resent, setResent] = useState(false);
  const [resentError, setResentError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    api
      .verifyEmail(token)
      .then(() => setStatus("success"))
      .catch(() => setStatus("error"));
  }, [token]);

  const resend = async (event: FormEvent) => {
    event.preventDefault();
    setResentError(null);
    try {
      await api.requestVerification(email);
      setResent(true);
    } catch (caught) {
      setResentError(caught instanceof ApiError ? caught.message : "Erro inesperado");
    }
  };

  return (
    <div className="w-full max-w-sm rounded-lg border border-border bg-card p-8 shadow-sm text-center">
      {status === "verifying" && <p className="text-muted-foreground">Verificando…</p>}
      {status === "success" && (
        <>
          <h1 className="mb-2 text-2xl font-semibold text-card-foreground">E-mail verificado!</h1>
          <p className="mb-4 text-muted-foreground">
            Sua conta está ativa. Você já pode fazer login.
          </p>
          <a href="/login" className="text-primary hover:underline text-sm">
            Ir para o login
          </a>
        </>
      )}
      {status === "error" && (
        <>
          <h1 className="mb-2 text-2xl font-semibold text-card-foreground">Link inválido</h1>
          <p className="text-muted-foreground">O link expirou ou já foi usado.</p>
        </>
      )}
      {status === "pending" && (
        <>
          <h1 className="mb-2 text-2xl font-semibold text-card-foreground">Verifique seu e-mail</h1>
          <p className="mb-6 text-muted-foreground">
            Enviamos um link de ativação para o seu e-mail. Clique no link para ativar sua conta.
          </p>
          {resent ? (
            <output className="text-sm text-primary">
              Link reenviado! Verifique sua caixa de entrada.
            </output>
          ) : (
            <form onSubmit={resend} className="flex flex-col gap-3 text-left">
              <label htmlFor="resend-email" className="text-sm font-medium text-foreground">
                Reenviar para
              </label>
              <input
                id="resend-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
              {resentError !== null && <p role="alert">{resentError}</p>}
              <button
                type="submit"
                className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
              >
                Reenviar link
              </button>
            </form>
          )}
        </>
      )}
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-4">
      <Suspense fallback={<p className="text-muted-foreground">Carregando…</p>}>
        <VerifyEmailContent />
      </Suspense>
    </main>
  );
}
