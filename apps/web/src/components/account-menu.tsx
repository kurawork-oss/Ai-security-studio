"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { authConfigured, supabase } from "@/lib/supabase";

export function AccountMenu() {
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    const client = supabase();
    if (!client) return;
    client.auth.getSession().then(({ data }) => setEmail(data.session?.user?.email ?? null));
    const { data } = client.auth.onAuthStateChange((_event, session) =>
      setEmail(session?.user?.email ?? null),
    );
    return () => data.subscription.unsubscribe();
  }, []);

  async function signOut() {
    const client = supabase();
    if (client) await client.auth.signOut();
    window.location.href = "/sign-in";
  }

  if (!authConfigured) {
    return <span className="text-xs text-[var(--muted)]">dev モード</span>;
  }
  if (!email) {
    return (
      <Link href="/sign-in" className="text-sm text-[var(--muted)] hover:underline">
        サインイン
      </Link>
    );
  }
  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="text-[var(--muted)]">{email}</span>
      <button onClick={signOut} className="text-[var(--muted)] hover:underline">
        サインアウト
      </button>
    </div>
  );
}
