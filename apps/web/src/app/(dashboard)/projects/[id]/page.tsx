"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  AnalyticsSummary,
  ApiKey,
  ApiKeyIssued,
  LogEntry,
  Project,
  Provider,
  Rule,
  api,
} from "@/lib/mgmt";

export default function ProjectDetail({ params }: { params: { id: string } }) {
  const id = params.id;
  const [project, setProject] = useState<Project | null>(null);
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [rules, setRules] = useState<Rule[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [issued, setIssued] = useState<ApiKeyIssued | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [p, k, r, pv, s, lg] = await Promise.all([
        api.getProject(id),
        api.listApiKeys(id),
        api.listRules(id),
        api.listProviders(id),
        api.analyticsSummary(id),
        api.listLogs(id),
      ]);
      setProject(p);
      setKeys(k);
      setRules(r);
      setProviders(pv);
      setSummary(s);
      setLogs(lg);
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

      {summary && (
        <Section title="Analytics">
          <div className="grid grid-cols-3 gap-3">
            <Stat label="リクエスト" value={String(summary.requests)} />
            <Stat label="Protect 件数" value={String(summary.protectCount)} />
            <Stat label="平均レイテンシ" value={`${summary.avgLatencyMs}ms`} />
          </div>
          {Object.keys(summary.entityCounts).length > 0 && (
            <div className="mt-4">
              <p className="mb-2 text-xs text-[var(--muted)]">検出内訳（種別別）</p>
              {Object.entries(summary.entityCounts)
                .sort((a, b) => b[1] - a[1])
                .map(([code, v]) => {
                  const max = Math.max(...Object.values(summary.entityCounts));
                  return <Bar key={code} label={code} value={v} pct={max ? (v / max) * 100 : 0} />;
                })}
            </div>
          )}
        </Section>
      )}

      {logs.length > 0 && (
        <Section title="最近のログ（メタデータのみ）">
          <div className="divide-y divide-[var(--border)] rounded-md border border-[var(--border)] text-sm">
            {logs.map((l) => (
              <div key={l.id} className="flex items-center justify-between p-2">
                <span className="font-mono text-xs">
                  {l.endpoint} · {l.statusCode}
                </span>
                <span className="text-xs text-[var(--muted)]">{l.latencyMs}ms</span>
              </div>
            ))}
          </div>
        </Section>
      )}

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

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-[var(--border)] p-3">
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-xs text-[var(--muted)]">{label}</div>
    </div>
  );
}

function Bar({ label, value, pct }: { label: string; value: number; pct: number }) {
  return (
    <div className="mb-1 flex items-center gap-2 text-xs">
      <span className="w-40 shrink-0 font-mono">{label}</span>
      <span className="h-2 flex-1 rounded bg-black/5">
        <span
          className="block h-2 rounded bg-brand"
          style={{ width: `${Math.max(4, pct)}%` }}
        />
      </span>
      <span className="w-8 text-right text-[var(--muted)]">{value}</span>
    </div>
  );
}
