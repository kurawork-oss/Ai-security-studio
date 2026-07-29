import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <p className="mb-3 inline-block rounded-full border border-[var(--border)] px-3 py-1 text-xs text-[var(--muted)]">
        AI Security Platform
      </p>
      <h1 className="text-4xl font-bold tracking-tight">SecureAI Studio</h1>
      <p className="mt-4 text-lg text-[var(--muted)]">
        AI へデータを送る<strong className="text-brand"> 前 </strong>に、PII を自動で検出・匿名化する
        共通セキュリティレイヤー。
      </p>
      <p className="mt-2 text-sm text-[var(--muted)]">
        中核思想：「AI へ送る前に、必ず SecureAI を通す」
      </p>

      <div className="mt-8 flex gap-3">
        <Link
          href="/playground"
          className="rounded-md bg-brand px-4 py-2 text-sm font-medium text-white hover:opacity-90"
        >
          Protect Playground を試す →
        </Link>
        <a
          href="https://github.com/kurawork-oss/Ai-security-studio/tree/main/docs"
          className="rounded-md border border-[var(--border)] px-4 py-2 text-sm hover:bg-black/5"
        >
          設計ドキュメント
        </a>
      </div>

      <section className="mt-12 grid gap-4 sm:grid-cols-2">
        <Card title="Pattern A — Protect API" body="既に AI を使う開発者向け。マスク済みデータを返し、送信は自分で。" />
        <Card title="Pattern B — Analyze API" body="AI 未導入向け。マスク → 登録済みプロバイダー → 分析結果まで。" />
      </section>
    </main>
  );
}

function Card({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-lg border border-[var(--border)] p-4">
      <h3 className="font-semibold">{title}</h3>
      <p className="mt-1 text-sm text-[var(--muted)]">{body}</p>
    </div>
  );
}
