"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { ApiKey, ApiKeyIssued, Project, Provider, Rule, api } from "@/lib/mgmt";

export default function ProjectDetail({ params }: { params: { id: string } }) {
  const id = params.id;
  const [project, setProject] = useState<Project | null>(null);
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [rules, setRules] = useState<Rule[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [issued, setIssued] = useState<ApiKeyIssued | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [p, k, r, pv] = await Promise.all([
        api.getProject(id),
        api.listApiKeys(id),
        api.listRules(id),
        api.listProviders(id),
      ]);
      setProject(p);
      setKeys(k);
      setRules(r);
      setProviders(pv);
    } catch (e) {
      setError(e instanceof Error ? e.message : "読み込みに失敗しました");
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  async function issue(keyType: string) {
    setIssued(await api.issueApiKey(id, keyType));
    await load();
  }
  async function revoke(keyId: string) {
    await api.revokeApiKey(keyId);
    await load();
  }
  function toggle(entityType: string) {
    setRules((rs) =>
      rs.map((r) => (r.entityType === entityType ? { ...r, enabled: !r.enabled } : r)),
    );
  }
  async function saveRules() {
    setRules(await api.updateRules(id, rules));
  }
  async function addEcho() {
    await api.createProvider(id, { providerType: "echo", displayName: "Echo (dev)" });
    await load();
  }

  if (error) return <p className="text-sm text-red-500">{error}</p>;
  if (!project) return <p className="text-sm text-[var(--muted)]">読み込み中…</p>;

  return (
    <div className="mx-auto max-w-3xl">
      <Link href="/projects" className="text-sm text-[var(--muted)]">
        ← Projects
      </Link>
      <h1 className="mt-2 text-2xl font-bold">{project.name}</h1>
      <p className="font-mono text-xs text-[var(--muted)]">{project.slug}</p>

      {issued && (
        <div className="mt-4 rounded-md border border-brand bg-brand/10 p-3 text-sm">
          <p className="font-medium">API キーを発行しました（一度だけ表示されます）</p>
          <code className="mt-1 block break-all">{issued.apiKey}</code>
        </div>
      )}

      <Section title="API Keys">
        <div className="mb-3 flex gap-2">
          <button onClick={() => issue("protect")} className="btn">
            Protect キー発行
          </button>
          <button onClick={() => issue("analyze")} className="btn">
            Analyze キー発行
          </button>
        </div>
        <List
          empty="キーがありません"
          items={keys.map((k) => ({
            key: k.id,
            left: `${k.keyType} · ${k.keyPrefix}…`,
            right:
              k.status === "active" ? (
                <button onClick={() => revoke(k.id)} className="text-xs text-red-500">
                  失効
                </button>
              ) : (
                <span className="text-xs text-[var(--muted)]">revoked</span>
              ),
          }))}
        />
      </Section>

      <Section title="Providers">
        <button onClick={addEcho} className="btn mb-3">
          Echo プロバイダー追加
        </button>
        <List
          empty="プロバイダーがありません"
          items={providers.map((p) => ({
            key: p.id,
            left: `${p.providerType} · ${p.displayName}`,
            right: <span className="text-xs text-[var(--muted)]">{p.isActive ? "active" : "off"}</span>,
          }))}
        />
      </Section>

      <Section title="Protect Rules">
        <div className="flex flex-wrap gap-2">
          {rules.map((r) => (
            <button
              key={r.entityType}
              onClick={() => toggle(r.entityType)}
              className={`rounded-full border px-3 py-1 text-xs ${
                r.enabled ? "border-brand bg-brand/10 text-brand" : "border-[var(--border)] text-[var(--muted)]"
              }`}
            >
              {r.enabled ? "●" : "○"} {r.entityType}
            </button>
          ))}
        </div>
        <button onClick={saveRules} className="btn mt-3">
          ルールを保存
        </button>
      </Section>

      <style>{`.btn{border:1px solid var(--border);border-radius:0.375rem;padding:0.4rem 0.8rem;font-size:0.8rem}`}</style>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-8">
      <h2 className="mb-3 text-sm font-semibold">{title}</h2>
      {children}
    </section>
  );
}

function List({
  items,
  empty,
}: {
  items: { key: string; left: string; right: React.ReactNode }[];
  empty: string;
}) {
  if (items.length === 0) return <p className="text-sm text-[var(--muted)]">{empty}</p>;
  return (
    <div className="divide-y divide-[var(--border)] rounded-md border border-[var(--border)]">
      {items.map((i) => (
        <div key={i.key} className="flex items-center justify-between p-3 text-sm">
          <span className="font-mono text-xs">{i.left}</span>
          {i.right}
        </div>
      ))}
    </div>
  );
}
