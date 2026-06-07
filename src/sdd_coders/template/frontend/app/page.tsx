import Link from "next/link";

export default function HomePage() {
  return (
    <main>
      <h1>Bem-vindo</h1>
      <nav>
        <Link href="/login">Entrar</Link>
        <Link href="/register">Criar conta</Link>
      </nav>
    </main>
  );
}
