"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, Boxes, KeyRound, Plus, ScrollText, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
    setRules((rs) => rs.map((r) => (r.entityType === entityType ? { ...r, enabled: !r.enabled } : r)));
  }
  async function saveRules() {
    setRules(await api.updateRules(id, rules));
  }
  async function addEcho() {
    await api.createProvider(id, { providerType: "echo", displayName: "Echo (dev)" });
    await load();
  }

  if (error) return <p className="text-sm text-destructive">{error}</p>;
  if (!project) return <p className="text-sm text-muted-foreground">読み込み中…</p>;

  const maxEntity = summary ? Math.max(1, ...Object.values(summary.entityCounts)) : 1;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <Link
          href="/projects"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="size-4" /> Projects
        </Link>
        <h1 className="mt-2 text-2xl font-bold tracking-tight">{project.name}</h1>
        <p className="font-mono text-xs text-muted-foreground">{project.slug}</p>
      </div>

      {issued && (
        <Card className="border-primary/40 bg-primary/5">
          <CardContent className="pt-5">
            <p className="text-sm font-medium">API キーを発行しました（この画面でのみ表示されます）</p>
            <div className="mt-2 flex items-center gap-2">
              <code className="flex-1 break-all rounded-md bg-background px-3 py-2 font-mono text-xs">
                {issued.apiKey}
              </code>
              <Button
                size="sm"
                variant="outline"
                onClick={() => navigator.clipboard?.writeText(issued.apiKey)}
              >
                コピー
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* API Keys */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <KeyRound className="size-4 text-primary" /> API Keys
          </CardTitle>
          <CardDescription>Protect / Analyze を分離して発行・失効します。</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="protect">
            <TabsList>
              <TabsTrigger value="protect">Protect</TabsTrigger>
              <TabsTrigger value="analyze">Analyze</TabsTrigger>
            </TabsList>
            {["protect", "analyze"].map((type) => (
              <TabsContent key={type} value={type}>
                <Button size="sm" className="mb-3" onClick={() => issue(type)}>
                  <Plus className="size-4" /> {type} キー発行
                </Button>
                <KeyList keys={keys.filter((k) => k.keyType === type)} onRevoke={revoke} />
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>

      {/* Providers */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Boxes className="size-4 text-primary" /> Providers
          </CardTitle>
          <CardDescription>LLM プロバイダー（Gemini / Claude / OpenAI / echo）。</CardDescription>
        </CardHeader>
        <CardContent>
          <Button size="sm" variant="outline" className="mb-3" onClick={addEcho}>
            <Plus className="size-4" /> Echo プロバイダー追加
          </Button>
          {providers.length === 0 ? (
            <p className="text-sm text-muted-foreground">プロバイダーがありません。</p>
          ) : (
            <div className="divide-y rounded-md border">
              {providers.map((p) => (
                <div key={p.id} className="flex items-center justify-between p-3 text-sm">
                  <span className="font-mono text-xs">
                    {p.providerType} · {p.displayName}
                  </span>
                  <Badge variant={p.isActive ? "success" : "secondary"}>
                    {p.isActive ? "active" : "off"}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Protect Rules */}
      <Card>
        <CardHeader>
          <CardTitle>Protect Rules</CardTitle>
          <CardDescription>検出・匿名化する PII 種別を切り替えます。</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
            {rules.map((r) => (
              <label
                key={r.entityType}
                className="flex cursor-pointer items-center justify-between gap-3"
              >
                <span className="font-mono text-xs">{r.entityType}</span>
                <Switch checked={r.enabled} onCheckedChange={() => toggle(r.entityType)} />
              </label>
            ))}
          </div>
          <Button size="sm" className="mt-5" onClick={saveRules}>
            ルールを保存
          </Button>
        </CardContent>
      </Card>

      {/* Analytics */}
      {summary && (
        <Card>
          <CardHeader>
            <CardTitle>Analytics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-3">
              <Stat label="リクエスト" value={String(summary.requests)} />
              <Stat label="Protect 件数" value={String(summary.protectCount)} />
              <Stat label="平均レイテンシ" value={`${summary.avgLatencyMs}ms`} />
            </div>
            {Object.keys(summary.entityCounts).length > 0 && (
              <div className="mt-5">
                <p className="mb-2 text-xs text-muted-foreground">検出内訳（種別別）</p>
                {Object.entries(summary.entityCounts)
                  .sort((a, b) => b[1] - a[1])
                  .map(([code, v]) => (
                    <div key={code} className="mb-1.5 flex items-center gap-2 text-xs">
                      <span className="w-40 shrink-0 font-mono">{code}</span>
                      <span className="h-2 flex-1 overflow-hidden rounded bg-muted">
                        <span
                          className="block h-2 rounded bg-primary"
                          style={{ width: `${Math.max(4, (v / maxEntity) * 100)}%` }}
                        />
                      </span>
                      <span className="w-8 text-right text-muted-foreground">{v}</span>
                    </div>
                  ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Logs */}
      {logs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ScrollText className="size-4 text-primary" /> 最近のログ
            </CardTitle>
            <CardDescription>メタデータのみ（生 PII は保存しません）。</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="divide-y rounded-md border text-sm">
              {logs.map((l) => (
                <div key={l.id} className="flex items-center justify-between p-2.5">
                  <span className="font-mono text-xs">
                    {l.endpoint} · {l.statusCode}
                  </span>
                  <span className="text-xs text-muted-foreground">{l.latencyMs}ms</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function KeyList({ keys, onRevoke }: { keys: ApiKey[]; onRevoke: (id: string) => void }) {
  if (keys.length === 0) return <p className="text-sm text-muted-foreground">キーがありません。</p>;
  return (
    <div className="divide-y rounded-md border">
      {keys.map((k) => (
        <div key={k.id} className="flex items-center justify-between p-3 text-sm">
          <span className="font-mono text-xs">{k.keyPrefix}…</span>
          {k.status === "active" ? (
            <Button variant="ghost" size="sm" onClick={() => onRevoke(k.id)}>
              <Trash2 className="size-4 text-destructive" />
            </Button>
          ) : (
            <Badge variant="secondary">revoked</Badge>
          )}
        </div>
      ))}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border p-3">
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  );
}
