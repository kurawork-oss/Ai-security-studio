import { AccountMenu } from "@/components/account-menu";
import { Sidebar } from "@/components/layout/sidebar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="bg-canvas flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 flex h-14 items-center justify-between border-b border-border/70 bg-background/70 px-6 backdrop-blur-md">
          <span className="text-sm font-medium text-muted-foreground">管理コンソール</span>
          <AccountMenu />
        </header>
        <main className="flex-1 px-6 py-8">{children}</main>
      </div>
    </div>
  );
}
