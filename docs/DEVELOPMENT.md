# 開発ガイド

モノレポ構成: `apps/api`（FastAPI）/ `apps/web`（Next.js）/ `infra/supabase`（DB）。

> ツールチェーン: MVP では **npm workspaces**（`package-lock.json`）で運用しています。
> 設計上の目標は pnpm + Turborepo（[ライブラリ構成](./architecture/10-library-stack.md)）で、
> `turbo.json` は将来導入用に同梱済みです。

## 実装状況（スライス①）

| 領域 | 状態 |
| --- | --- |
| API: Protect / Analyze / Detect | ✅ 実装・テスト済（pytest 17件緑） |
| PII エンジン（Regex + 検証器） | ✅ 12種・Luhn/マイナンバー/法人番号チェック |
| Provider Interface（echo / gemini） | ✅ |
| API キー（Protect/Analyze 分離・認可） | ✅ |
| フェイルクローズ | ✅ テストで保証 |
| DB マイグレーション + seed（Supabase） | ✅ PG パーサ検証済（未適用） |
| Web: ランディング + Protect Playground | ✅ 雛形（BFF 経由でキー秘匿） |
| 管理画面 CRUD / Supabase 結線 / SDK / Export / Plugin | ⏳ 次スライス |

## API（FastAPI）

```bash
cd apps/api
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
cp .env.example .env
.venv/bin/uvicorn src.main:app --reload   # http://localhost:8000
.venv/bin/pytest -q
```

詳細は [apps/api/README.md](../apps/api/README.md)。

## Web（Next.js）

```bash
cd apps/web
npm install
cp .env.example .env.local            # SECUREAI_API_BASE_URL / SECUREAI_PROTECT_KEY を設定
npm run dev                           # http://localhost:3000  → /playground
```

Playground はブラウザから **BFF（`/api/playground/*`）** 経由で API を呼ぶため、
API キーはサーバー側に留まりブラウザへ露出しません。

## Supabase（DB）

```bash
# Supabase CLI を利用（例）
supabase start
supabase db reset          # infra/supabase/migrations/*.sql を適用
psql "$DATABASE_URL" -f infra/supabase/seed.sql
```

- スキーマ: [`infra/supabase/migrations/0001_init.sql`](../infra/supabase/migrations/0001_init.sql)
- RLS: [`0002_rls.sql`](../infra/supabase/migrations/0002_rls.sql)
- 設計との対応: [DB 設計](./architecture/03-database-design.md)

## 環境変数

各アプリの `.env.example` を参照。**ハードコード禁止**・秘密情報はコミットしない。
