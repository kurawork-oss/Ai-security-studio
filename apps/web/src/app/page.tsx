import Link from "next/link";
import { ArrowRight, Boxes, KeyRound, ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function Home() {
  return (
    <main className="min-h-screen">
      <div className="container py-20">
        <Badge variant="secondary" className="mb-4">
          AI Security Platform
        </Badge>
        <h1 className="max-w-3xl text-4xl font-bold tracking-tight sm:text-5xl">
          AI へ送る前に、<span className="text-primary">必ず SecureAI を通す</span>
        </h1>
        <p className="mt-4 max-w-xl text-lg text-muted-foreground">
          Gemini・Claude・OpenAI へデータを送る前に、PII（個人情報）を自動で検出・匿名化する
          共通セキュリティレイヤー。
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Button asChild size="lg">
            <Link href="/playground">
              Protect Playground を試す
              <ArrowRight className="size-4" />
            </Link>
          </Button>
          <Button asChild size="lg" variant="outline">
            <Link href="/projects">管理コンソール</Link>
          </Button>
        </div>

        <div className="mt-16 grid gap-4 sm:grid-cols-3">
          <Feature
            icon={ShieldCheck}
            title="Pattern A — Protect"
            body="既に AI を使う開発者向け。マスク済みデータを返し、送信は自分で。"
          />
          <Feature
            icon={Boxes}
            title="Pattern B — Analyze"
            body="AI 未導入向け。マスク → 登録済みプロバイダー → 分析結果まで。"
          />
          <Feature
            icon={KeyRound}
            title="拡張性と安全性"
            body="Provider / Rule / Plugin を後付け。生 PII は永続化しない。"
          />
        </div>
      </div>
    </main>
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
    <Card>
      <CardContent className="pt-5">
        <span className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Icon className="size-5" />
        </span>
        <h3 className="mt-3 font-semibold">{title}</h3>
        <p className="mt-1 text-sm text-muted-foreground">{body}</p>
      </CardContent>
    </Card>
  );
}
