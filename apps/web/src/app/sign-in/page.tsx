"use client";

import Link from "next/link";
import { useState } from "react";
import { authConfigured, supabase } from "@/lib/supabase";

export default function SignIn() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState<string | null>(null);

  async function signIn() {
    const c = supabase();
    if (!c) return;
    const { error } = await c.auth.signInWithPassword({ email, password });
    setMsg(error ? error.message : "サインインしました。/projects へ移動できます。");
  }

  return (
    <main className="mx-auto max-w-sm px-6 py-16">
      <h1 className="text-2xl font-bold">サインイン</h1>

      {!authConfigured ? (
        <div className="mt-4 rounded-md border border-[var(--border)] p-4 text-sm text-[var(--muted)]">
          Supabase Auth は未設定です（開発モード）。
          <br />
          管理 API は <code>SECUREAI_DEV_JWT</code> のフォールバックで動作します。
          <div className="mt-3">
            <Link href="/projects" className="text-brand">
              → Projects へ
            </Link>
          </div>
        </div>
      ) : (
        <div className="mt-6 flex flex-col gap-3">
          <input
            className="rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
            placeholder="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <input
            type="password"
            className="rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
            placeholder="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button onClick={signIn} className="rounded-md bg-brand px-4 py-2 text-sm font-medium text-white">
            サインイン
          </button>
          {msg && <p className="text-sm text-[var(--muted)]">{msg}</p>}
        </div>
      )}
    </main>
  );
}
