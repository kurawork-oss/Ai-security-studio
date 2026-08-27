"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authConfigured, supabase } from "@/lib/supabase";

export default function SignIn() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState<string | null>(null);

  async function signIn() {
    const c = supabase();
    if (!c) return;
    const { error } = await c.auth.signInWithPassword({ email, password });
    if (error) setMsg(error.message);
    else router.push("/projects");
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>サインイン</CardTitle>
          <CardDescription>SecureAI Studio 管理コンソール</CardDescription>
        </CardHeader>
        <CardContent>
          {!authConfigured ? (
            <div className="text-sm text-muted-foreground">
              Supabase Auth は未設定です（開発モード）。管理 API は{" "}
              <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">
                SECUREAI_DEV_JWT
              </code>{" "}
              のフォールバックで動作します。
              <div className="mt-4">
                <Button asChild variant="outline" className="w-full">
                  <Link href="/projects">Projects へ</Link>
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="space-y-1.5">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="pw">Password</Label>
                <Input
                  id="pw"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
              <Button className="w-full" onClick={signIn}>
                サインイン
              </Button>
              {msg && <p className="text-sm text-destructive">{msg}</p>}
            </div>
          )}
        </CardContent>
      </Card>
    </main>
  );
}
