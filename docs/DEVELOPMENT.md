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
| **Plugin 基盤（Extractor/Delivery）+ Extract/Batch/Streaming/Webhook** | ✅ 実装・テスト済 |
| **SDK（Python `secureai` / JS `@secureai/sdk`）** | ✅ Python pytest・JS `tsc` ビルド |
| **Export Module（Claude Code/Codex/Cursor/Windsurf）** | ✅ 実装・テスト済 |
| **マルチプロバイダー（Gemini / Claude / OpenAI）** | ✅ アダプタ実装・テスト済 |
| **Plugin: PDF / Word / Excel 抽出** | ✅ `.[extractors]` で有効化・テスト済 |
| **Analytics 可視化（Dashboard）** | ✅ 統計タイル・種別内訳バー・ログ |
| **Supabase Auth（RS256/JWKS + HS256）** | ✅ バックエンド検証・フロントのセッション/サインアウト |
| **CI（GitHub Actions）** | ✅ pytest / migrations / build を自動実行 |
| Plugin: OCR / Audio / RAG / MCP | 🧩 マニフェスト宣言（stub・optional 実装） |

テスト: backend `pytest 51件緑`（うち 4 件は実 Postgres 統合）＋ Python SDK `5件`。`next build`・SDK `tsc`・CI 通過。

認証（管理 API）: トークンの `alg` に応じて **RS256/ES256（JWKS）** と **HS256（secret）** を
自動選択。本番は `SECUREAI_SUPABASE_URL`（→ JWKS 自動解決）、開発は `SECUREAI_SUPABASE_JWT_SECRET`。

PDF/Word/Excel 抽出は optional。`pip install -e ".[extractors]"`（pypdf/python-docx/
openpyxl）で有効化され、`GET /v1/plugins` の `available` が true になります。未導入時は
stub 宣言のみ（`/v1/extract` は 400 を返す）。

プロバイダーは `providers.provider_type` で解決（`gemini`/`claude`/`openai`/`echo`）。
`openai` アダプタは OpenAI 互換（DeepSeek/Grok/local）にも流用可能。`default_model` は
env かプロジェクト設定で指定（モデル名はハードコードしない）。

### Plugin エンドポイント

- `GET /v1/plugins` — 利用可能プラグイン一覧（`available` フラグ）
- `POST /v1/extract` — content（base64）→ 抽出 → **マスクして返却**（CSV/JSON/HTML/plaintext）
- `POST /v1/protect` `/v1/analyze` — `contentType` + `contentBase64` でファイル入力も可
- `POST /v1/batch/analyze` — 複数テキストの一括分析
- `POST /v1/analyze/stream` — 逐次ストリーミング（匿名化は先行実行＝fail-closed）

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

## SDK

REST の型付きラッパー。`packages/sdk-python`（`secureai`）と `packages/sdk-js`（`@secureai/sdk`）。

```python
from secureai import SecureAI
client = SecureAI(api_key="sk_protect_...", base_url="http://localhost:8000")
print(client.protect("田中太郎 090-1234-5678").masked_text)
```
```ts
import { SecureAI } from "@secureai/sdk";
const client = new SecureAI("sk_protect_...", { baseUrl: "http://localhost:8000" });
const { maskedText } = await client.protect("田中太郎 090-1234-5678");
```

- Python テスト: `cd packages/sdk-python && pytest`（httpx MockTransport で API 不要）
- JS 型検証/ビルド: `npm run -w @secureai/sdk build`

## Export API（AI コーディングツール向けプロンプト生成）

- `GET /v1/export/targets` — 対応ターゲット（claude_code / codex / cursor / windsurf）
- `POST /v1/projects/{id}/export` — `{ targetId, language, pattern, apiBaseUrl }` → プロンプト
- 生成物に**実キーは含めず**、環境変数プレースホルダのみ。

## 環境変数

各アプリの `.env.example` を参照。**ハードコード禁止**・秘密情報はコミットしない。
