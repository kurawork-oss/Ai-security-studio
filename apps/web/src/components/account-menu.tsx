"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { LogOut } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
    return <Badge variant="secondary">dev モード</Badge>;
  }
  if (!email) {
    return (
      <Button asChild variant="outline" size="sm">
        <Link href="/sign-in">サインイン</Link>
      </Button>
    );
  }
  return (
    <div className="flex items-center gap-2">
      <span className="hidden text-sm text-muted-foreground sm:inline">{email}</span>
      <Button variant="ghost" size="sm" onClick={signOut}>
        <LogOut className="size-4" />
        サインアウト
      </Button>
    </div>
  );
}
