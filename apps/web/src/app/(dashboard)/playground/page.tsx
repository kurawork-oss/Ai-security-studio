"use client";

import { useState } from "react";
import { Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { ENTITY_TYPES, ProtectResult, runProtect } from "@/lib/playground-client";

const SAMPLE =
  "山田花子さんの連絡先は taro@example.com、電話 090-1234-5678、" +
  "カード番号 4242 4242 4242 4242、住所 東京都千代田区1-1、〒100-0001 です。";

export default function PlaygroundPage() {
  const [text, setText] = useState(SAMPLE);
  const [rules, setRules] = useState<Record<string, boolean>>(
    Object.fromEntries(ENTITY_TYPES.map((e) => [e.code, true])),
  );
  const [result, setResult] = useState<ProtectResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const detected = result?.entities?.length ?? 0;

  async function onProtect() {
    setLoading(true);
    setError(null);
    try {
      setResult(await runProtect(text, rules));
    } catch (e) {
      setError(e instanceof Error ? e.message : "エラーが発生しました");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Protect Playground</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          貼り付け → ルール ON/OFF → 保護実行 → 置換をリアルタイムでプレビュー。
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">入力テキスト</CardTitle>
          </CardHeader>
          <CardContent>
            <Textarea
              className="h-56 resize-none"
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
            <div className="mt-3 flex gap-2">
              <Button onClick={onProtect} disabled={loading || text.trim().length === 0}>
                <Sparkles className="size-4" />
                {loading ? "保護中…" : "保護実行"}
              </Button>
              <Button variant="outline" onClick={() => setText(SAMPLE)}>
                サンプル投入
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm">保護後プレビュー</CardTitle>
            {result && <Badge variant="success">検出 {detected}</Badge>}
          </CardHeader>
          <CardContent>
            <pre className="h-56 overflow-auto whitespace-pre-wrap rounded-md border bg-muted/40 p-3 text-sm">
              {error ? (
                <span className="text-destructive">{error}</span>
              ) : (
                result?.maskedText ?? "（ここに結果が表示されます）"
              )}
            </pre>
            {result && (
              <p className="mt-2 font-mono text-xs text-muted-foreground">{result.requestId}</p>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="mt-4">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Protect ルール</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {ENTITY_TYPES.map((e) => {
              const on = rules[e.code];
              return (
                <button
                  key={e.code}
                  onClick={() => setRules((r) => ({ ...r, [e.code]: !r[e.code] }))}
                  className={cn(
                    "rounded-full border px-3 py-1 text-xs transition-all",
                    on
                      ? "bg-brand-soft border-primary/30 font-medium text-primary shadow-sm"
                      : "border-border text-muted-foreground hover:bg-accent hover:text-foreground",
                  )}
                >
                  {on ? "●" : "○"} {e.label}
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {result?.entities && result.entities.length > 0 && (
        <Card className="mt-4">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">検出内訳</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="grid gap-1 text-sm sm:grid-cols-2">
              {result.entities.map((s, i) => (
                <li key={i} className="flex justify-between rounded-md border px-3 py-1.5">
                  <span className="font-mono text-xs">{s.entityType}</span>
                  <span className="text-xs text-muted-foreground">score {s.score.toFixed(2)}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
