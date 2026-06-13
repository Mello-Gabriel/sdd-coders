"use client";

import { api } from "@/lib/api/client";
import { useRouter } from "next/navigation";
import { useState } from "react";

/** LGPD self-service: export personal data, or delete (anonymise) the account. */
export function AccountData() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [confirming, setConfirming] = useState(false);

  const onExport = async () => {
    setError("");
    try {
      const data = await api.exportData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "meus-dados.json";
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      setError("Não foi possível exportar seus dados.");
    }
  };

  const onDelete = async () => {
    setError("");
    try {
      await api.deleteAccount();
      router.push("/login");
    } catch {
      setError("Não foi possível excluir sua conta.");
    }
  };

  return (
    <div className="space-y-4">
      <button
        type="button"
        onClick={onExport}
        className="rounded-md border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-muted"
      >
        Exportar meus dados
      </button>

      <div>
        {confirming ? (
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              Esta ação é irreversível. Seus dados pessoais serão anonimizados.
            </p>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={onDelete}
                className="rounded-md bg-destructive px-4 py-2 text-sm font-medium text-destructive-foreground hover:opacity-90"
              >
                Confirmar exclusão
              </button>
              <button
                type="button"
                onClick={() => setConfirming(false)}
                className="rounded-md border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-muted"
              >
                Cancelar
              </button>
            </div>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setConfirming(true)}
            className="rounded-md border border-destructive px-4 py-2 text-sm font-medium text-destructive hover:bg-destructive hover:text-destructive-foreground"
          >
            Excluir minha conta
          </button>
        )}
      </div>

      {error && <output className="text-sm text-destructive">{error}</output>}
    </div>
  );
}
