import { LogoutButton } from "@/components/logout-button";
import { ProjectList } from "@/components/project-list";
import { ThemeToggle } from "@/components/theme-toggle";

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card px-6 py-4 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-card-foreground">Meus projetos</h1>
        <div className="flex items-center gap-2">
          <a href="/settings" className="text-sm text-muted-foreground hover:text-foreground">
            Configurações
          </a>
          <ThemeToggle />
          <LogoutButton />
        </div>
      </header>
      <main className="mx-auto max-w-4xl p-6">
        <ProjectList />
      </main>
    </div>
  );
}
