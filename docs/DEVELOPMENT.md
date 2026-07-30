# 開発ガイド

モノレポ構成: `apps/api`（FastAPI）/ `apps/web`（Next.js）/ `infra/supabase`（DB）。

> ツールチェーン: MVP では **npm workspaces**（`package-lock.json`）で運用しています。
> 設計上の目標は pnpm + Turborepo（[ライブラリ構成](./architecture/10-library-stack.md)）で、
> `turbo.json` は将来導入用に同梱済みです。

## 実装状況

| 領域 | 状態 |
| --- | --- |
| API: Protect / Analyze / Detect | ✅ 実装・テスト済 |
| PII エンジン（Regex + 検証器） | ✅ 12種・Luhn/マイナンバー/法人番号チェック |
| Provider Interface（echo / gemini） | ✅ |
| API キー（Protect/Analyze 分離・認可） | ✅ |
| フェイルクローズ | ✅ テストで保証 |
| **Postgres 永続化（SQLAlchemy async リポジトリ）** | ✅ 実 PG で統合テスト |
| **管理 API（Projects/Providers/API Keys/Rules/Logs/Analytics）** | ✅ JWT 認証・テナント分離 |
| **ログ永続化** | ✅ data-plane が logs に記録 |
| DB マイグレーション + seed（Supabase） | ✅ 実 PostgreSQL 16 に適用・検証済 |
| Web: ランディング + Protect Playground | ✅ BFF 経由でキー秘匿 |
| **Web: Dashboard（Projects/API Keys/Protect Rules/Providers）** | ✅ 管理 BFF 経由・`next build` 通過 |
| SDK / Export / Plugin / マルチプロバイダー | ⏳ 次スライス |

テスト: `pytest 21件緑`（うち 4 件は実 Postgres 統合）。`next build` 通過。管理〜データ平面の E2E 確認済み。

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

### Postgres モードで起動

`SECUREAI_DATABASE_URL` を設定すると in-memory ではなく Postgres を使います。
管理 API は Supabase JWT（`SECUREAI_SUPABASE_JWT_SECRET`）で認証します。

```bash
SECUREAI_DATABASE_URL=postgresql+asyncpg://USER:PASS@HOST:5432/DB \
SECUREAI_SUPABASE_JWT_SECRET=... \
.venv/bin/uvicorn src.main:app --reload
```

## Supabase / Postgres（DB）

```bash
# Supabase を使う場合
supabase start
supabase db reset          # infra/supabase/migrations/*.sql を適用
psql "$DATABASE_URL" -f infra/supabase/seed.sql
```

Supabase を使わずローカル Postgres で試す場合は、`auth` スキーマの互換シムを先に適用します。

```bash
psql "$DATABASE_URL" -f infra/supabase/local/00_local_shim.sql   # 開発専用
psql "$DATABASE_URL" -f infra/supabase/migrations/0001_init.sql
psql "$DATABASE_URL" -f infra/supabase/migrations/0002_rls.sql
psql "$DATABASE_URL" -f infra/supabase/seed.sql
```

- スキーマ: [`0001_init.sql`](../infra/supabase/migrations/0001_init.sql) / RLS: [`0002_rls.sql`](../infra/supabase/migrations/0002_rls.sql)
- ローカルシム（Supabase 非使用時のみ）: [`local/00_local_shim.sql`](../infra/supabase/local/00_local_shim.sql)
- 統合テスト: `SECUREAI_TEST_DATABASE_URL=postgresql+asyncpg://…/testdb pytest`（未設定時は自動 skip）
- 設計との対応: [DB 設計](./architecture/03-database-design.md)

## 環境変数

各アプリの `.env.example` を参照。**ハードコード禁止**・秘密情報はコミットしない。
