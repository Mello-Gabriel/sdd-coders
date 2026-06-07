"use client";

import { api } from "@/lib/api/client";
import { useRouter } from "next/navigation";

export function LogoutButton() {
  const router = useRouter();

  const onClick = async () => {
    await api.logout();
    router.push("/login");
  };

  return (
    <button type="button" onClick={onClick}>
      Sair
    </button>
  );
}
