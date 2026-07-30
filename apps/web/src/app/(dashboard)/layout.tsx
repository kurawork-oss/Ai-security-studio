import Link from "next/link";

const NAV = [
  { href: "/projects", label: "Projects" },
  { href: "/playground", label: "Protect Playground" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <aside className="w-56 shrink-0 border-r border-[var(--border)] p-4">
        <Link href="/" className="block text-lg font-bold text-brand">
          SecureAI
        </Link>
        <p className="mb-6 text-xs text-[var(--muted)]">Studio</p>
        <nav className="flex flex-col gap-1">
          {NAV.map((n) => (
            <Link
              key={n.href}
              href={n.href}
              className="rounded-md px-3 py-2 text-sm hover:bg-black/5"
            >
              {n.label}
            </Link>
          ))}
        </nav>
      </aside>
      <div className="flex-1">
        <header className="flex h-14 items-center justify-between border-b border-[var(--border)] px-6">
          <span className="text-sm text-[var(--muted)]">管理コンソール</span>
          <Link href="/sign-in" className="text-sm text-[var(--muted)] hover:underline">
            アカウント
          </Link>
        </header>
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}
