# ④ API 設計

## 方針

- **REST / JSON**、バージョンは URL プレフィックス `/{version}`（現行 `v1`）。
- **2 系統の認証**:
  - **Data Plane**（Protect/Analyze）… SecureAI 発行の **API キー**（`Authorization: Bearer sk_live_...`）。
  - **Control Plane**（管理 API）… Supabase Auth の **JWT**（`Authorization: Bearer <jwt>`）。
- **統一エラー形式**・**統一ページネーション**・**OpenAPI 自動生成**（FastAPI）。
- **将来 GraphQL 移行**を想定し、ユースケース層を薄くラップする設計（後述 §7）。

## 1. Data Plane API

### `POST /v1/protect`
PII を検出・匿名化し、マスク済みテキストを返す。

**Request**
```json
{
  "text": "田中太郎さんのメールは taro@example.com です",
  "options": { "returnEntities": false }
}
```

**Response `200`**
```json
{
  "maskedText": "<PERSON_1>さんのメールは <EMAIL_1> です",
  "requestId": "req_01J...",
  "entities": null
}
```

> 仕様上の最小契約は `{ "maskedText": "..." }`。`requestId`・`entities` は付加情報で、
> `options.returnEntities=true` の時のみ `entities`（種別・位置・スコア）を返す（生値は含めない）。

### `POST /v1/analyze`
マスク → 登録済みプロバイダーへ送信 → 分析結果を返す。

**Request**
```json
{
  "text": "顧客 山田花子 の問い合わせ内容を要約して",
  "options": { "providerId": "prov_...", "model": "gemini-1.5-pro", "deanonymize": true }
}
```

**Response `200`**
```json
{
  "analysis": "問い合わせは配送遅延に関する内容で…",
  "requestId": "req_01J...",
  "usage": { "inputTokens": 128, "outputTokens": 64 }
}
```

- `providerId` 省略時はプロジェクト既定プロバイダーを使用。
- `deanonymize=true` の場合、**リクエスト内の一時マップ** で応答中のプレースホルダを実値へ復元（永続化なし・`D-3`）。
- **フェイルクローズ**: 匿名化失敗時は LLM へ送らず `502 ANONYMIZATION_FAILED` を返す。

### `POST /v1/detect`（補助・任意）
匿名化せず検出結果のみ返す（デバッグ・プレビュー用途）。Playground でも使用。

## 2. Control Plane API（管理）

すべて JWT 認証。テナントは JWT から解決し RLS で保護。

| メソッド | パス | 説明 |
| --- | --- | --- |
| `GET` | `/v1/me` | 自身のプロフィール・所属 org |
| `GET/POST` | `/v1/projects` | プロジェクト一覧 / 作成 |
| `GET/PATCH/DELETE` | `/v1/projects/{id}` | 取得 / 更新 / アーカイブ |
| `GET/POST` | `/v1/projects/{id}/providers` | プロバイダー一覧 / 登録 |
| `PATCH/DELETE` | `/v1/providers/{id}` | 更新 / 削除 |
| `GET/POST` | `/v1/providers/{id}/keys` | プロバイダーキー一覧 / 登録（暗号化保存） |
| `POST` | `/v1/providers/{id}/keys/{keyId}/rotate` | キーのローテーション |
| `DELETE` | `/v1/providers/{id}/keys/{keyId}` | キー失効 |
| `GET/POST` | `/v1/projects/{id}/api-keys?type=protect\|analyze` | SecureAI キー一覧 / 発行（`keyType` 指定・**平文は作成時のみ返却**） |
| `POST` | `/v1/api-keys/{id}/rotate` | ローテーション（新キー発行 + 旧キーへ `rotated_from` 設定） |
| `POST` | `/v1/api-keys/{id}/revoke` | キー失効 |
| `GET` | `/v1/export/targets` / `POST /v1/projects/{id}/export` | Export（[⑦](./13-export-module.md)） |
| `GET/PUT` | `/v1/projects/{id}/protect-rules` | ルール取得 / 一括更新（bulk upsert） |
| `GET` | `/v1/projects/{id}/logs` | ログ一覧（フィルタ・ページネーション） |
| `GET` | `/v1/projects/{id}/analytics/summary` | サマリ指標 |
| `GET` | `/v1/projects/{id}/analytics/timeseries` | 時系列（リクエスト数・レイテンシ・検出数） |
| `GET` | `/v1/pii-entity-types` | PII エンティティカタログ |

### API キー発行のレスポンス（作成時のみ平文）
```json
{
  "id": "key_...",
  "name": "prod-server",
  "apiKey": "sk_live_9f3a...ONLY_SHOWN_ONCE",
  "keyPrefix": "sk_live_9f3a",
  "scopes": ["protect", "analyze"],
  "createdAt": "2026-07-29T00:00:00Z"
}
```

## 3. 統一エラー形式

すべてのエラーは同一形状で返す（`core/errors.py` の統一ハンドラ）。

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Retry after 12s.",
    "requestId": "req_01J...",
    "details": { "retryAfterSeconds": 12 }
  }
}
```

| HTTP | code 例 | 意味 |
| --- | --- | --- |
| 400 | `VALIDATION_ERROR` | 入力不正（サイズ超過・型不一致） |
| 401 | `UNAUTHENTICATED` | キー/JWT 不正・失効 |
| 403 | `FORBIDDEN` | スコープ/テナント権限なし |
| 404 | `NOT_FOUND` | リソース不在 |
| 409 | `CONFLICT` | 一意制約違反（slug 重複等） |
| 422 | `UNPROCESSABLE` | 意味的に処理不能 |
| 429 | `RATE_LIMIT_EXCEEDED` | レート制限 |
| 502 | `ANONYMIZATION_FAILED` | 匿名化失敗（LLM 未送信） |
| 502 | `PROVIDER_ERROR` | 上流 LLM エラー |
| 500 | `INTERNAL_ERROR` | 予期せぬ内部エラー |

## 4. 横断仕様

- **ページネーション**: カーソル方式 `?limit=50&cursor=...` → `{ data: [...], nextCursor, hasMore }`。
- **べき等性**: `Protect/Analyze` は `Idempotency-Key` ヘッダ任意対応（重複課金防止）。
- **レート制限**: `X-RateLimit-Limit / -Remaining / -Reset` を返却。プロジェクト×キー単位。
- **リクエスト ID**: 全レスポンスに `requestId`（`X-Request-Id`）。ログ・サポートで追跡。
- **入力上限**: `text` は既定 100KB（環境変数で調整）。超過は `413/400`。
- **CORS**: Dashboard オリジンのみ許可。Data Plane はサーバー間利用前提で CORS を絞る。

## 5. バージョニング

- 破壊的変更時のみ `v2` を追加。`v1` は非推奨期間を設けて併存。
- レスポンスへのフィールド追加は破壊的変更としない（クライアントは寛容に読む）。

## 6. 統合コード例（"数行で" の体験）

**JavaScript / TypeScript**
```ts
const res = await fetch("https://api.secureai.studio/v1/protect", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${process.env.SECUREAI_API_KEY}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ text: userInput }),
});
const { maskedText } = await res.json();
// maskedText を Gemini へ送信
```

**Python**
```python
import os, httpx
r = httpx.post(
    "https://api.secureai.studio/v1/protect",
    headers={"Authorization": f"Bearer {os.environ['SECUREAI_API_KEY']}"},
    json={"text": user_input},
)
masked_text = r.json()["maskedText"]
```

将来は薄い SDK（`@secureai/sdk`, `secureai`）を提供予定（[ロードマップ](./07-roadmap.md)）。

## 7. GraphQL 移行の布石

- HTTP ルーターは **ユースケース層（application）を呼ぶだけ** の薄い層に保つ。
- GraphQL 導入時は Strawberry 等のリゾルバから同じユースケースを呼ぶ（ビジネスロジックの二重化なし）。
- スキーマは OpenAPI（REST）と GraphQL SDL の両方を、ドメインの型から機械生成できる構成を目標。

## 8. API キーの分離とローテーション（⑧）

- **用途分離**: Project 毎に **Protect 用キー** と **Analyze 用キー** を別々に発行（[DB: `api_keys`](./03-database-design.md)）。
  - `POST /v1/protect` は `key_type=protect`、`POST /v1/analyze` は `key_type=analyze` のみ受理（不一致は `403 FORBIDDEN`）。
  - プレフィックスで判別可能: `sk_protect_...` / `sk_analyze_...`。
- **ローテーション**: `POST /v1/api-keys/{id}/rotate` で新キーを発行し、旧キーは `rotated_from` で連結。
  猶予期間中は新旧両方が有効 → 期限で旧キーを `revoke`。**無停止**でキー切替できる。
- **監査**: 発行・ローテーション・失効・閲覧は `audit_logs` に記録。

## 9. SDK / Export / 将来拡張

- **SDK**（[⑥](./12-sdk-design.md)）: 本 REST 設計（安定エンベロープ・`error.code`・`Idempotency-Key`・カーソル・OpenAPI）は
  JS / Python / Node SDK 生成の前提を満たす。
- **Export**（[⑦](./13-export-module.md)）: プロジェクト設定から AI コーディングツール向けプロンプトを生成。
- **将来拡張は Plugin 経由**（[⑪](./14-plugin-architecture.md)）:
  - `POST /v1/analyze:stream`（Streaming Response）
  - `POST /v1/batch/analyze`（Batch Analyze）
  - ファイル入力（PDF/Word/Excel/OCR/Image/Audio）、MCP エンドポイント公開、Webhook 通知。
  - いずれも **送信前の匿名化（フェイルクローズ）** を必ず通す。
