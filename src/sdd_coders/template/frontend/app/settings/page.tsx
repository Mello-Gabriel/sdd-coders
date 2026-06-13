import { AccountData } from "@/components/account-data";
import { ChangePasswordForm } from "@/components/change-password-form";
import { PrivacySettings } from "@/components/privacy-settings";
import { ThemeToggle } from "@/components/theme-toggle";

export default function SettingsPage() {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card px-6 py-4 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-card-foreground">Configurações</h1>
        <div className="flex items-center gap-2">
          <a href="/dashboard" className="text-sm text-muted-foreground hover:text-foreground">
            Dashboard
          </a>
          <ThemeToggle />
        </div>
      </header>
      <main className="mx-auto max-w-2xl p-6 space-y-10">
        <section>
          <h2 className="mb-4 text-base font-semibold text-foreground">Alterar senha</h2>
          <ChangePasswordForm />
        </section>
        <section>
          <h2 className="mb-4 text-base font-semibold text-foreground">Privacidade e cookies</h2>
          <PrivacySettings />
        </section>
        <section>
          <h2 className="mb-4 text-base font-semibold text-foreground">Meus dados (LGPD)</h2>
          <AccountData />
        </section>
      </main>
    </div>
  );
}
