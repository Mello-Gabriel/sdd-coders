import { LogoutButton } from "@/components/logout-button";
import { ProjectList } from "@/components/project-list";

export default function DashboardPage() {
  return (
    <main>
      <h1>Meus projetos</h1>
      <LogoutButton />
      <ProjectList />
    </main>
  );
}
