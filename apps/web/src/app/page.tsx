import Link from "next/link";
import {
  ArrowRight,
  Boxes,
  FileLock2,
  Lock,
  Plug,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function Home() {
  return (
    <main className="bg-canvas min-h-screen">
      <SiteNav />

      {/* Hero */}
      <section className="container relative pt-16 pb-10 sm:pt-24">
        <div className="mx-auto max-w-3xl text-center">
          <span className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-brand-soft px-3.5 py-1.5 text-xs font-medium text-primary shadow-sm">
            <span className="relative flex size-2">
              <span className="absolute inline-flex size-full animate-ping rounded-full bg-primary/60" />
              <span className="relative inline-flex size-2 rounded-full bg-primary" />
            </span>
            AI Security Platform
          </span>

          <h1 className="mt-6 text-balance text-4xl font-bold leading-[1.1] tracking-tight sm:text-6xl">
            AI へ送る前に、
            <br className="hidden sm:block" />
            <span className="text-gradient">必ず SecureAI を通す</span>
          </h1>

          <p className="mx-auto mt-6 max-w-xl text-pretty text-lg leading-relaxed text-muted-foreground">
            Gemini・Claude・OpenAI へデータを送る前に、PII（個人情報）を自動で検出・匿名化する
            <span className="font-medium text-foreground">共通セキュリティレイヤー</span>。
          </p>

          <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
            <Button asChild size="lg">
              <Link href="/playground">
                <Sparkles className="size-4" />
                Protect Playground を試す
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link href="/projects">
                管理コンソール
                <ArrowRight className="size-4" />
              </Link>
            </Button>
          </div>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-muted-foreground">
            <TrustItem icon={ShieldCheck} label="PII 12 種を検出・匿名化" />
            <TrustItem icon={Lock} label="AES-256-GCM 暗号化" />
            <TrustItem icon={FileLock2} label="生 PII は永続化しない" />
          </div>
        </div>
      </section>

      {/* Flow diagram */}
      <section className="container pb-8">
        <FlowDiagram />
      </section>

      {/* Features */}
      <section className="container py-16">
        <div className="mx-auto mb-10 max-w-2xl text-center">
          <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
            2 つの使い方、1 つの安全な入口
          </h2>
          <p className="mt-3 text-muted-foreground">
            既に AI を使う開発者にも、これから導入するチームにも。
          </p>
        </div>
        <div className="grid gap-5 sm:grid-cols-3">
          <Feature
            icon={ShieldCheck}
            eyebrow="Pattern A"
            title="Protect"
            body="マスク済みデータを返し、送信は自分で。既存の AI 連携にそのまま差し込めます。"
          />
          <Feature
            icon={Boxes}
            eyebrow="Pattern B"
            title="Analyze"
            body="マスク → 登録済みプロバイダー → 分析結果まで。AI 未導入でもすぐに。"
          />
          <Feature
            icon={Plug}
            eyebrow="Extensible"
            title="拡張性と安全性"
            body="Provider / Rule / Plugin を後付け。監査ログはメタデータのみを保存。"
          />
        </div>
      </section>

      <SiteFooter />
    </main>
  );
}

function SiteNav() {
  return (
    <header className="sticky top-0 z-20 border-b border-border/60 bg-background/70 backdrop-blur-md">
      <div className="container flex h-16 items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5">
          <span className="bg-brand flex size-8 items-center justify-center rounded-lg text-primary-foreground shadow-brand">
            <ShieldCheck className="size-4" />
          </span>
          <span className="text-[15px] font-bold tracking-tight">
            SecureAI
            <span className="ml-1 text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
              Studio
            </span>
          </span>
        </Link>
        <div className="flex items-center gap-2">
          <Button asChild variant="ghost" size="sm" className="hidden sm:inline-flex">
            <Link href="/playground">Playground</Link>
          </Button>
          <Button asChild size="sm">
            <Link href="/projects">
              管理コンソール
              <ArrowRight className="size-4" />
            </Link>
          </Button>
        </div>
      </div>
    </header>
  );
}

function TrustItem({
  icon: Icon,
  label,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
}) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <Icon className="size-3.5 text-primary" />
      {label}
    </span>
  );
}

function FlowDiagram() {
  return (
    <div className="mx-auto max-w-4xl">
      <div className="grid items-stretch gap-3 md:grid-cols-[1fr_auto_1.1fr_auto_1fr]">
        {/* Source */}
        <FlowCard tone="danger" label="あなたのデータ" title="生 PII を含む">
          <div className="space-y-1.5 font-mono text-[11px] text-muted-foreground">
            <p>山田花子</p>
            <p>taro@example.com</p>
            <p>090-1234-5678</p>
          </div>
        </FlowCard>

        <FlowArrow />

        {/* SecureAI */}
        <div className="bg-brand relative overflow-hidden rounded-xl p-[1.5px] shadow-brand">
          <div className="relative flex h-full flex-col rounded-[10px] bg-card p-5">
            <span className="bg-brand inline-flex size-9 items-center justify-center rounded-lg text-primary-foreground shadow-sm">
              <ShieldCheck className="size-5" />
            </span>
            <p className="mt-3 text-[11px] font-semibold uppercase tracking-wider text-primary">
              SecureAI
            </p>
            <p className="text-sm font-semibold">検出 → 匿名化</p>
            <div className="mt-3 space-y-1.5 font-mono text-[11px]">
              <p className="text-foreground">
                <span className="text-gradient font-semibold">&lt;PERSON_1&gt;</span>
              </p>
              <p className="text-foreground">
                <span className="text-gradient font-semibold">&lt;EMAIL_ADDRESS_1&gt;</span>
              </p>
              <p className="text-foreground">
                <span className="text-gradient font-semibold">&lt;PHONE_NUMBER_1&gt;</span>
              </p>
            </div>
          </div>
        </div>

        <FlowArrow />

        {/* AI providers */}
        <FlowCard tone="plain" label="安全に送信" title="AI プロバイダー">
          <div className="flex flex-wrap gap-1.5">
            {["Gemini", "Claude", "OpenAI"].map((p) => (
              <span
                key={p}
                className="rounded-md border border-border bg-muted/60 px-2 py-1 text-[11px] font-medium"
              >
                {p}
              </span>
            ))}
          </div>
        </FlowCard>
      </div>
    </div>
  );
}

function FlowCard({
  tone,
  label,
  title,
  children,
}: {
  tone: "danger" | "plain";
  label: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col rounded-xl border bg-card p-5 shadow-card">
      <p
        className={
          "text-[11px] font-semibold uppercase tracking-wider " +
          (tone === "danger" ? "text-destructive/80" : "text-muted-foreground")
        }
      >
        {label}
      </p>
      <p className="text-sm font-semibold">{title}</p>
      <div className="mt-3">{children}</div>
    </div>
  );
}

function FlowArrow() {
  return (
    <div className="flex items-center justify-center py-1 md:py-0">
      <span className="bg-brand-soft flex size-8 rotate-90 items-center justify-center rounded-full text-primary md:rotate-0">
        <ArrowRight className="size-4" />
      </span>
    </div>
  );
}

function Feature({
  icon: Icon,
  eyebrow,
  title,
  body,
}: {
  icon: React.ComponentType<{ className?: string }>;
  eyebrow: string;
  title: string;
  body: string;
}) {
  return (
    <Card className="hover-lift hover:border-primary/30 hover:shadow-card-lg">
      <CardContent className="pt-6">
        <span className="bg-brand-soft flex size-11 items-center justify-center rounded-xl text-primary ring-1 ring-inset ring-primary/15">
          <Icon className="size-5" />
        </span>
        <p className="mt-4 text-[11px] font-semibold uppercase tracking-wider text-primary">
          {eyebrow}
        </p>
        <h3 className="mt-0.5 text-lg font-semibold tracking-tight">{title}</h3>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{body}</p>
      </CardContent>
    </Card>
  );
}

function SiteFooter() {
  return (
    <footer className="border-t border-border/60">
      <div className="container flex flex-col items-center justify-between gap-3 py-8 sm:flex-row">
        <div className="flex items-center gap-2 text-sm">
          <span className="bg-brand flex size-6 items-center justify-center rounded-md text-primary-foreground">
            <ShieldCheck className="size-3.5" />
          </span>
          <span className="font-semibold">SecureAI Studio</span>
        </div>
        <p className="text-xs text-muted-foreground">
          AI へ送る前に、必ず SecureAI を通す。
        </p>
      </div>
    </footer>
  );
}
