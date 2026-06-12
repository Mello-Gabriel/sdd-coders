import { AdminUsers } from "@/components/admin-users";
import { ThemeToggle } from "@/components/theme-toggle";

export default function AdminPage() {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card px-6 py-4 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-card-foreground">Administração</h1>
        <div className="flex items-center gap-2">
          <a href="/dashboard" className="text-sm text-muted-foreground hover:text-foreground">
            Dashboard
          </a>
          <ThemeToggle />
        </div>
      </header>
      <main className="mx-auto max-w-4xl p-6">
        <AdminUsers />
      </main>
    </div>
  );
}
