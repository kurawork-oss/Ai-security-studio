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
    <aside className="hidden w-60 shrink-0 flex-col border-r bg-sidebar p-3 md:flex">
      <Link href="/" className="mb-6 flex items-center gap-2.5 px-2 py-2">
        <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Shield className="size-4" />
        </span>
        <span>
          <span className="block text-sm font-bold leading-tight">SecureAI</span>
          <span className="block text-[10px] uppercase tracking-wide text-muted-foreground">
            Studio
          </span>
        </span>
      </Link>
      <nav className="flex flex-col gap-1">
        {NAV.map((n) => {
          const active = pathname === n.href || pathname.startsWith(n.href + "/");
          const Icon = n.icon;
          return (
            <Link
              key={n.href}
              href={n.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-primary/10 font-medium text-primary"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground",
              )}
            >
              <Icon className="size-4" />
              {n.label}
            </Link>
          );
        })}
      </nav>
      <p className="mt-auto px-3 py-2 text-[11px] leading-relaxed text-muted-foreground">
        AI へ送る前に、
        <br />
        必ず SecureAI を通す
      </p>
    </aside>
  );
}
