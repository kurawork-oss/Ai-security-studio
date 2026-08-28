import Link from "next/link";
import { ArrowRight, Boxes, Plug, ShieldCheck, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function Home() {
  return (
    <main className="bg-canvas min-h-screen">
      <SiteNav />

      {/* Hero */}
      <section className="container relative pt-20 pb-12 text-center sm:pt-28">
        <h1 className="mx-auto max-w-3xl animate-in fade-in slide-in-from-bottom-3 text-balance text-4xl font-bold leading-[1.12] tracking-tight duration-700 sm:text-6xl">
          AI へ送る前に、
          <br className="hidden sm:block" />
          <span className="text-gradient">必ず SecureAI を通す</span>
        </h1>
        <p className="mx-auto mt-5 max-w-md animate-in fade-in slide-in-from-bottom-3 text-pretty text-lg text-muted-foreground delay-100 duration-700 fill-mode-both">
          個人情報を自動でマスクしてから、AI に送る。
        </p>
        <div className="mt-8 flex animate-in fade-in slide-in-from-bottom-3 flex-wrap items-center justify-center gap-3 delay-200 duration-700 fill-mode-both">
          <Button asChild size="lg">
            <Link href="/playground">
              <Sparkles className="size-4" />
              試してみる
            </Link>
          </Button>
          <Button asChild size="lg" variant="outline">
            <Link href="/projects">
              管理コンソール
              <ArrowRight className="size-4" />
            </Link>
          </Button>
        </div>
      </section>

      {/* Flow — how it works, at a glance */}
      <section className="container animate-in fade-in slide-in-from-bottom-4 pb-16 delay-300 duration-1000 fill-mode-both">
        <p className="mb-5 text-center text-sm font-medium text-muted-foreground">
          個人情報は、AI に届く前にマスクされます
        </p>
        <FlowDiagram />
      </section>

      {/* Features — minimal */}
      <section className="container pb-20">
        <div className="mx-auto grid max-w-4xl gap-4 sm:grid-cols-3">
          <Feature icon={ShieldCheck} title="Protect" body="マスクして返す" />
          <Feature icon={Boxes} title="Analyze" body="分析まで任せる" />
          <Feature icon={Plug} title="拡張" body="後付けで機能追加" />
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

function FlowDiagram() {
  return (
    <div className="mx-auto max-w-4xl">
      <div className="grid items-stretch gap-3 md:grid-cols-[1fr_auto_1.1fr_auto_1fr]">
        {/* Input */}
        <FlowCard tone="danger" label="入力" title="生データ">
          <div className="space-y-1 font-mono text-[11px] text-muted-foreground">
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
            <p className="mt-3 text-sm font-semibold text-primary">SecureAI が自動マスク</p>
            <div className="mt-3 space-y-1 font-mono text-[11px]">
              <p className="text-gradient font-semibold">&lt;PERSON_1&gt;</p>
              <p className="text-gradient font-semibold">&lt;EMAIL_ADDRESS_1&gt;</p>
              <p className="text-gradient font-semibold">&lt;PHONE_NUMBER_1&gt;</p>
            </div>
          </div>
        </div>

        <FlowArrow />

        {/* AI */}
        <FlowCard tone="plain" label="送信" title="AI">
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
  title,
  body,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  body: string;
}) {
  return (
    <Card className="hover-lift hover:border-primary/30 hover:shadow-card-lg">
      <CardContent className="flex items-center gap-3 py-5">
        <span className="bg-brand-soft flex size-11 shrink-0 items-center justify-center rounded-xl text-primary ring-1 ring-inset ring-primary/15">
          <Icon className="size-5" />
        </span>
        <div>
          <h3 className="font-semibold tracking-tight">{title}</h3>
          <p className="text-sm text-muted-foreground">{body}</p>
        </div>
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
        <p className="text-xs text-muted-foreground">AI へ送る前に、必ず SecureAI を通す。</p>
      </div>
    </footer>
  );
}
