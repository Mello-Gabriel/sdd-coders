/** API contract types (kept in sync with the backend Pydantic schemas). */

export interface User {
  id: string;
  email: string;
  role: string;
  is_active: boolean;
  email_verified: boolean;
}

export interface Project {
  id: string;
  owner_id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface AuditEntry {
  id: string;
  occurred_at: string;
  actor_id: string | null;
  actor_role: string;
  action: string;
  entity_type: string;
  entity_id: string | null;
}

export interface UserUpdate {
  is_active?: boolean;
  role?: "user" | "admin";
}
