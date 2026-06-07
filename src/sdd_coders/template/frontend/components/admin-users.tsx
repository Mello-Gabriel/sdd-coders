"use client";

import { api } from "@/lib/api/client";
import type { User } from "@/lib/api/types";
import { useEffect, useState } from "react";

export function AdminUsers() {
  const [users, setUsers] = useState<User[]>([]);

  useEffect(() => {
    void api.listUsers().then(setUsers);
  }, []);

  const toggle = async (user: User) => {
    const updated = await api.updateUser(user.id, { is_active: !user.is_active });
    setUsers((current) => current.map((item) => (item.id === updated.id ? updated : item)));
  };

  return (
    <table>
      <tbody>
        {users.map((user) => (
          <tr key={user.id}>
            <td>{user.email}</td>
            <td>{user.is_active ? "ativo" : "inativo"}</td>
            <td>
              <button type="button" onClick={() => toggle(user)}>
                {user.is_active ? "Desativar" : "Ativar"}
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
