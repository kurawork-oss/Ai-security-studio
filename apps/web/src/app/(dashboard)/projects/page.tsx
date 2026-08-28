"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ChevronRight, FolderKanban, Plus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Project, api } from "@/lib/mgmt";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setProjects(await api.listProjects());
    } catch (e) {
      setError(e instanceof Error ? e.message : "読み込みに失敗しました");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function create() {
    if (!name.trim()) return;
    try {
      await api.createProject(name.trim());
      setName("");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "作成に失敗しました");
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Projects</h1>
        <p className="mt-1 text-sm text-muted-foreground">キー・ルール・プロバイダーを管理。</p>
      </div>

      <div className="flex gap-2">
        <Input
          placeholder="新規プロジェクト名"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && create()}
        />
        <Button onClick={create} disabled={!name.trim()}>
          <Plus className="size-4" />
          作成
        </Button>
      </div>

      {error && <p className="mt-3 text-sm text-destructive">{error}</p>}

      <div className="mt-6 space-y-2">
        {loading ? (
          [0, 1, 2].map((i) => <Skeleton key={i} className="h-[68px] w-full" />)
        ) : projects.length === 0 ? (
          <Card className="p-10 text-center">
            <p className="text-sm font-medium">まだプロジェクトがありません</p>
            <p className="mt-1 text-sm text-muted-foreground">上の入力欄から作成してください。</p>
          </Card>
        ) : (
          projects.map((p) => (
            <Link key={p.id} href={`/projects/${p.id}`} className="block">
              <Card className="hover-lift flex items-center justify-between p-4 hover:border-primary/30 hover:shadow-card-lg">
                <div className="flex items-center gap-3">
                  <span className="bg-brand-soft flex size-10 items-center justify-center rounded-xl text-primary ring-1 ring-inset ring-primary/15">
                    <FolderKanban className="size-5" />
                  </span>
                  <div>
                    <div className="font-semibold tracking-tight">{p.name}</div>
                    <div className="font-mono text-xs text-muted-foreground">{p.slug}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">{p.environment}</Badge>
                  <ChevronRight className="size-4 text-muted-foreground" />
                </div>
              </Card>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
