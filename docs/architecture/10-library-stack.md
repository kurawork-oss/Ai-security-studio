# ⑩ ライブラリ構成

> 方針: **ハードコード禁止 / 環境変数で設定 / 型安全 / 依存は最小限に固定**。
> バージョンは着手時に最新安定へ固定（lockfile 管理）。以下は採用ライブラリと役割。

## Frontend（`apps/web`）

| 分類 | ライブラリ | 役割 |
| --- | --- | --- |
| フレームワーク | `next`（App Router）, `react`, `react-dom` | UI / RSC |
| 言語 | `typescript`（strict） | 型安全 |
| スタイル | `tailwindcss`, `tailwind-merge`, `clsx`, `tailwindcss-animate` | ユーティリティ CSS |
| UI | `shadcn/ui`（`@radix-ui/*`）, `lucide-react` | コンポーネント / アイコン |
| フォーム/検証 | `react-hook-form`, `zod`, `@hookform/resolvers` | フォーム・スキーマ検証 |
| データ取得 | `@tanstack/react-query` | サーバ状態管理・キャッシュ |
| 状態（軽量） | `zustand` | UI ローカル状態 |
| 認証/DB | `@supabase/supabase-js`, `@supabase/ssr` | Auth / クライアント |
| API 型 | `openapi-typescript`（+ 型付き fetch） | OpenAPI → TS 型生成 |
| チャート | `recharts` | Analytics 可視化 |
| 通知 | `sonner` | Toast |
| 日付 | `date-fns` | 日付整形 |
| フォント | `next/font`（Inter / JetBrains Mono） | セルフホスト |
| テスト | `vitest`, `@testing-library/react`, `playwright` | unit / e2e |
| 品質 | `eslint`, `typescript-eslint`, `prettier` | Lint / 整形 |

## Backend（`apps/api`）

| 分類 | ライブラリ | 役割 |
| --- | --- | --- |
| フレームワーク | `fastapi`, `uvicorn[standard]`, `gunicorn` | HTTP / ASGI |
| 設定/検証 | `pydantic` v2, `pydantic-settings` | DTO / 環境変数 |
| PII 検出 | `presidio-analyzer`, `presidio-anonymizer` | 検出 / 匿名化 |
| 日本語 NLP | `spacy`, `ja-ginza`（GiNZA） | 日本語 NER |
| DB | `sqlalchemy`(2.0 async), `asyncpg`, `alembic` | Repository 実装 / マイグレーション補助 |
| 認証 | `pyjwt`（+ JWKS）, `python-jose` | Supabase JWT 検証 |
| 暗号化 | `cryptography` | AES-256-GCM / 鍵導出 |
| LLM | `google-generativeai`（Gemini）, `httpx` | プロバイダー呼び出し |
| ログ | `structlog` | 構造化ログ統一 |
| 信頼性 | `tenacity` | リトライ |
| レート制限 | `slowapi`（Phase 2） | スロットリング |
| 監視 | `prometheus-client`, `sentry-sdk` | メトリクス / エラー追跡 |
| テスト | `pytest`, `pytest-asyncio`, `httpx`, `coverage` | テスト |
| 品質 | `ruff`, `black`, `mypy` | Lint / 整形 / 型 |

> 注: DB アクセスは `D-4` の推奨（SQLAlchemy async）。代替として `supabase-py`/PostgREST も可。
> DDL の真は Supabase migrations 側とし、Alembic は補助（[DB 設計 §5](./03-database-design.md)）。

## インフラ / ツールチェーン

| 分類 | ツール | 役割 |
| --- | --- | --- |
| モノレポ | `pnpm` workspaces, `turborepo` | タスク/依存管理 |
| DB/Auth | Supabase（`supabase` CLI） | Postgres / Auth / マイグレーション |
| コンテナ | Docker, docker-compose | ローカル/デプロイ |
| CI | GitHub Actions | lint / test / build / migration / security |
| セキュリティ | `gitleaks`, `pip-audit`, `npm audit`, `semgrep` | シークレット/脆弱性/SAST |

## 環境変数（`.env.example` に定義・値は含めない）

| 変数 | 用途 | 例/備考 |
| --- | --- | --- |
| `NEXT_PUBLIC_SUPABASE_URL` | Web → Supabase | 公開可 |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Web → Supabase | 公開可 |
| `NEXT_PUBLIC_API_BASE_URL` | Web → API | 例: `https://api.secureai.studio` |
| `SUPABASE_URL` | API → Supabase | |
| `SUPABASE_SERVICE_ROLE_KEY` | API（限定使用） | **秘匿** |
| `SUPABASE_JWT_JWKS_URL` / `SUPABASE_JWT_SECRET` | JWT 検証 | |
| `ENCRYPTION_KEK` | エンベロープ暗号の KEK | **秘匿**（KMS 推奨） |
| `GEMINI_API_BASE` | Gemini エンドポイント | ハードコード禁止 |
| `API_TEXT_MAX_BYTES` | 入力上限 | 既定 102400 |
| `RATE_LIMIT_*` | レート制限設定 | Phase 2 |
| `LOG_LEVEL` | ログレベル | `info` |
| `LOG_RETENTION_DAYS` | ログ保持日数 | 既定 90 |
| `SENTRY_DSN` | エラー監視 | 任意 |

すべての設定は `apps/web/src/config`（zod 検証）と `apps/api/src/core/config.py`（pydantic-settings）で
**起動時に検証** し、欠落・不正はフェイルファストで停止させます。
