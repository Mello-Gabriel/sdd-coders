import { AuthForm } from "@/components/auth-form";

export default function RegisterPage() {
  return (
    <main>
      <h1>Criar conta</h1>
      <AuthForm mode="register" />
    </main>
  );
}
