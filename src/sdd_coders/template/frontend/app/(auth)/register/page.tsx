import { AuthForm } from "@/components/auth-form";

export default function RegisterPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-sm rounded-lg border border-border bg-card p-8 shadow-sm">
        <h1 className="mb-6 text-2xl font-semibold text-card-foreground">Criar conta</h1>
        <AuthForm mode="register" turnstileSiteKey={process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY} />
        <p className="mt-4 text-center text-sm text-muted-foreground">
          Já tem uma conta?{" "}
          <a href="/login" className="text-primary hover:underline">
            Entrar
          </a>
        </p>
      </div>
    </main>
  );
}
