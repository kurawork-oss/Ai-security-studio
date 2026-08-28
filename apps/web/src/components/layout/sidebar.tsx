"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { FlaskConical, FolderKanban, Shield } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/projects", label: "Projects", icon: FolderKanban },
  { href: "/playground", label: "Protect Playground", icon: FlaskConical },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden w-60 shrink-0 flex-col border-r border-border/70 bg-sidebar p-3 md:flex">
      <Link href="/" className="mb-6 flex items-center gap-2.5 px-2 py-2">
        <span className="bg-brand flex size-8 items-center justify-center rounded-lg text-primary-foreground shadow-brand">
          <Shield className="size-4" />
        </span>
        <span>
          <span className="block text-sm font-bold leading-tight tracking-tight">SecureAI</span>
          <span className="block text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
            Studio
          </span>
        </span>
      </Link>
      <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/70">
        メニュー
      </p>
      <nav className="flex flex-col gap-1">
        {NAV.map((n) => {
          const active = pathname === n.href || pathname.startsWith(n.href + "/");
          const Icon = n.icon;
          return (
            <Link
              key={n.href}
              href={n.href}
              className={cn(
                "group flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all",
                active
                  ? "bg-brand-soft font-semibold text-primary shadow-sm ring-1 ring-inset ring-primary/15"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground",
              )}
            >
              <Icon className={cn("size-4 transition-colors", active && "text-primary")} />
              {n.label}
            </Link>
          );
        })}
      </nav>
      <div className="mt-auto rounded-lg border border-border/70 bg-brand-soft/40 p-3">
        <p className="flex items-center gap-1.5 text-[11px] font-medium text-primary">
          <Shield className="size-3" />
          Security first
        </p>
        <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">
          AI へ送る前に、必ず SecureAI を通す。
        </p>
      </div>
    </aside>
  );
}
