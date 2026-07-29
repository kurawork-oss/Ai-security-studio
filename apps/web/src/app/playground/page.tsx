"use client";

import { useState } from "react";
import {
  ENTITY_TYPES,
  ProtectResult,
  runProtect,
} from "@/lib/playground-client";

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
    <main className="mx-auto max-w-5xl px-6 py-10">
      <h1 className="text-2xl font-bold">Protect Playground</h1>
      <p className="mt-1 text-sm text-[var(--muted)]">
        テキストを貼り付け → ルールを ON/OFF → 保護実行 → 置換結果をプレビュー。
      </p>

      <div className="mt-6 grid gap-6 md:grid-cols-2">
        <div>
          <label className="text-sm font-medium">入力テキスト</label>
          <textarea
            className="mt-2 h-56 w-full rounded-md border border-[var(--border)] bg-transparent p-3 text-sm"
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <div className="mt-2 flex gap-2">
            <button
              onClick={onProtect}
              disabled={loading || text.trim().length === 0}
              className="rounded-md bg-brand px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              {loading ? "保護中…" : "保護実行"}
            </button>
            <button
              onClick={() => setText(SAMPLE)}
              className="rounded-md border border-[var(--border)] px-4 py-2 text-sm"
            >
              サンプル投入
            </button>
          </div>
        </div>

        <div>
          <label className="text-sm font-medium">保護後プレビュー</label>
          <pre className="mt-2 h-56 w-full overflow-auto rounded-md border border-[var(--border)] bg-black/5 p-3 text-sm whitespace-pre-wrap">
            {error ? (
              <span className="text-red-500">{error}</span>
            ) : (
              result?.maskedText ?? "（ここに結果が表示されます）"
            )}
          </pre>
          {result && (
            <p className="mt-2 text-xs text-[var(--muted)]">
              検出 {detected} 件 / requestId: {result.requestId}
            </p>
          )}
        </div>
      </div>

      <section className="mt-8">
        <h2 className="text-sm font-medium">Protect ルール</h2>
        <div className="mt-3 flex flex-wrap gap-2">
          {ENTITY_TYPES.map((e) => {
            const on = rules[e.code];
            return (
              <button
                key={e.code}
                onClick={() => setRules((r) => ({ ...r, [e.code]: !r[e.code] }))}
                className={`rounded-full border px-3 py-1 text-xs ${
                  on
                    ? "border-brand bg-brand/10 text-brand"
                    : "border-[var(--border)] text-[var(--muted)]"
                }`}
              >
                {on ? "●" : "○"} {e.label}
              </button>
            );
          })}
        </div>
      </section>

      {result?.entities && result.entities.length > 0 && (
        <section className="mt-8">
          <h2 className="text-sm font-medium">検出内訳</h2>
          <ul className="mt-3 grid gap-1 text-sm sm:grid-cols-2">
            {result.entities.map((s, i) => (
              <li
                key={i}
                className="flex justify-between rounded border border-[var(--border)] px-3 py-1"
              >
                <span className="font-mono text-xs">{s.entityType}</span>
                <span className="text-[var(--muted)]">score {s.score.toFixed(2)}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
