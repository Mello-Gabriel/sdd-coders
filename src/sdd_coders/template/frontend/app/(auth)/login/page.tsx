import { AuthForm } from "@/components/auth-form";

export default function LoginPage() {
  return (
    <main>
      <h1>Entrar</h1>
      <AuthForm mode="login" />
    </main>
  );
}
