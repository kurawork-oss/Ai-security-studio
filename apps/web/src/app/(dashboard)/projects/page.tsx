"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, Project } from "@/lib/mgmt";

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
      <h1 className="text-2xl font-bold">Projects</h1>
      <p className="mt-1 text-sm text-[var(--muted)]">
        プロジェクト単位で Provider・API キー・Protect ルールを管理します。
      </p>

      <div className="mt-6 flex gap-2">
        <input
          className="flex-1 rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
          placeholder="新規プロジェクト名"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <button
          onClick={create}
          className="rounded-md bg-brand px-4 py-2 text-sm font-medium text-white"
        >
          作成
        </button>
      </div>

      {error && <p className="mt-3 text-sm text-red-500">{error}</p>}

      <div className="mt-6 divide-y divide-[var(--border)] rounded-md border border-[var(--border)]">
        {loading ? (
          <p className="p-4 text-sm text-[var(--muted)]">読み込み中…</p>
        ) : projects.length === 0 ? (
          <p className="p-4 text-sm text-[var(--muted)]">まだありません。上で作成してください。</p>
        ) : (
          projects.map((p) => (
            <Link
              key={p.id}
              href={`/projects/${p.id}`}
              className="flex items-center justify-between p-4 hover:bg-black/5"
            >
              <span className="font-medium">{p.name}</span>
              <span className="font-mono text-xs text-[var(--muted)]">{p.slug}</span>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
