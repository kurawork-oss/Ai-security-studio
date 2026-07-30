"use client";

import { accessToken } from "./supabase";

export interface Project {
  id: string;
  name: string;
  slug: string;
  environment: string;
  status: string;
  createdAt?: string | null;
}
export interface ApiKey {
  id: string;
  name: string;
  keyType: string;
  keyPrefix: string;
  status: string;
  createdAt?: string | null;
}
export interface ApiKeyIssued extends ApiKey {
  apiKey: string;
}
export interface Rule {
  entityType: string;
  enabled: boolean;
  action: string;
  priority: number;
}
export interface Provider {
  id: string;
  providerType: string;
  displayName: string;
  defaultModel?: string | null;
  isActive: boolean;
}

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await accessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined),
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`/api/mgmt/${path}`, { ...init, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.error?.message ?? `Request failed (${res.status})`);
  }
  return res.status === 204 ? (null as T) : res.json();
}

export const api = {
  listProjects: () => req<Project[]>("projects"),
  createProject: (name: string) =>
    req<Project>("projects", { method: "POST", body: JSON.stringify({ name }) }),
  getProject: (id: string) => req<Project>(`projects/${id}`),
  listProviders: (id: string) => req<Provider[]>(`projects/${id}/providers`),
  createProvider: (id: string, body: Record<string, unknown>) =>
    req<Provider>(`projects/${id}/providers`, { method: "POST", body: JSON.stringify(body) }),
  listApiKeys: (id: string) => req<ApiKey[]>(`projects/${id}/api-keys`),
  issueApiKey: (id: string, keyType: string, name = "") =>
    req<ApiKeyIssued>(`projects/${id}/api-keys`, {
      method: "POST",
      body: JSON.stringify({ keyType, name }),
    }),
  revokeApiKey: (keyId: string) => req<null>(`api-keys/${keyId}/revoke`, { method: "POST" }),
  listRules: (id: string) => req<Rule[]>(`projects/${id}/protect-rules`),
  updateRules: (id: string, rules: Rule[]) =>
    req<Rule[]>(`projects/${id}/protect-rules`, {
      method: "PUT",
      body: JSON.stringify({ rules }),
    }),
};
