# SDK 設計（JavaScript / Python / Node）

> 設計レビュー依頼 **⑥** に対応。
> REST API だけでなく、将来 **JavaScript SDK / Python SDK / Node SDK** を提供する。
> 本書は「API 設計が SDK 前提になっているか」の確認と、SDK の共通仕様を定義する。

## 1. 方針

- **薄いラッパー** — SDK は [REST API](./04-api-design.md) の薄い型付きラッパー。ビジネスロジックはサーバ側に集約。
- **言語イディオム** — 各言語の慣習（例外/Promise/型）に沿う。
- **単一生成元** — OpenAPI から型・クライアントを機械生成し、手書き差分を最小化。
- **後方互換** — SemVer。破壊的変更は major のみ。フィールド追加は非破壊。

## 2. SDK が要求する API 特性（→ 現行 API 設計の適合確認）

| SDK 要件 | API 設計での担保 | 状態 |
| --- | --- | --- |
| 安定した JSON エンベロープ | Protect/Analyze の固定スキーマ（`maskedText` / `analysis`） | ✅ [§1](./04-api-design.md#1-data-plane-api) |
| 機械可読なエラー | `error.code` の enum + `requestId` | ✅ [§3](./04-api-design.md#3-統一エラー形式) |
| 再送安全性 | `Idempotency-Key` ヘッダ | ✅ [§4](./04-api-design.md#4-横断仕様) |
| ページネーション | カーソル方式（`nextCursor`） | ✅ [§4](./04-api-design.md#4-横断仕様) |
| バージョニング | URL `/v1`・非破壊追加 | ✅ [§5](./04-api-design.md#5-バージョニング) |
| 型生成 | `openapi.json` を公開（FastAPI 自動生成） | ✅ |
| 認証の一貫性 | `Authorization: Bearer <API Key>` | ✅（[キー分離](./04-api-design.md#8-api-キーの分離とローテーション)） |
| レート制限の可観測性 | `X-RateLimit-*` ヘッダ | ✅ |

> 結論: 現行 REST 設計は SDK 化に必要な要素（安定スキーマ・エラーコード・冪等・型生成元）を満たす。

## 3. 共通クライアント表面（言語横断の概念）

```
client = SecureAI(apiKey, { baseUrl?, timeout?, retries?, idempotencyKey? })

client.protect(text, options?)  -> { maskedText, requestId, entities? }
client.analyze(text, options?)  -> { analysis, requestId, usage }
client.detect(text, options?)   -> { entities, requestId }   // 補助
```

- **認証**: コンストラクタに API キー（Protect 用 / Analyze 用は用途で使い分け）。
- **エラー**: HTTP エラーは言語ネイティブの例外へマップ（`SecureAIError` 派生、`code` 保持）。
- **リトライ**: `429/5xx` を指数バックオフで自動リトライ（冪等操作のみ、上限設定可）。
- **セキュリティ**: API キーは **サーバサイド利用前提**。ブラウザへ直接埋め込まない旨をドキュメントで明示。

## 4. 言語別イメージ

### JavaScript / TypeScript（`@secureai/sdk`）
```ts
import { SecureAI } from "@secureai/sdk";
const client = new SecureAI({ apiKey: process.env.SECUREAI_PROTECT_KEY! });

const { maskedText } = await client.protect("田中太郎 090-1234-5678");
// maskedText を任意の LLM へ
```

### Python（`secureai`）
```python
from secureai import SecureAI
client = SecureAI(api_key=os.environ["SECUREAI_PROTECT_KEY"])

masked = client.protect("田中太郎 090-1234-5678").masked_text
```

### Node（サーバ用途）
- JS SDK と同一パッケージで動作（`fetch`/`undici` ベース）。ストリーミング対応時は `AsyncIterable` を返す。

## 5. パッケージング / リリース

| 言語 | パッケージ名（予定） | レジストリ |
| --- | --- | --- |
| JS/TS/Node | `@secureai/sdk` | npm |
| Python | `secureai` | PyPI |

- モノレポ `packages/sdk-js` / `packages/sdk-python`（または別リポジトリ）。
- CI で OpenAPI から型再生成 → SDK ビルド → 契約テスト（モックサーバ）→ 公開。
- 例やクイックスタートは Studio・[Export Module](./13-export-module.md) と連携。

## 6. 将来拡張

- `client.analyzeStream(...)`（[Plugin: Streaming](./14-plugin-architecture.md)）。
- `client.batchAnalyze(...)`（[Plugin: Batch](./14-plugin-architecture.md)）。
- ファイル入力（PDF/Word/Excel）ヘルパは Plugin 対応後に追加。
