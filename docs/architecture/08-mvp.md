# ⑧ MVP 定義

## ゴール

**「AI を使う前に SecureAI を通す」** という価値を、Gemini を対象に **通しで** 体験できること。
開発者が数行のコードで、PII をマスクしてから安全に Gemini を利用できる状態を最小構成で提供する。

## スコープ In（MVP に含む）

### 認証・テナント
- Supabase Auth によるサインアップ / ログイン / パスワード再設定。
- サインアップ時に個人 org を自動生成（UI 上は最小限）。

### 管理（Control Plane）
- Projects: 作成・一覧・詳細・アーカイブ。
- Providers: **Gemini** の登録、provider_keys の **暗号化保存**（末尾4桁のみ表示）。
- API Keys: 発行（**平文は1回のみ**表示）・失効。
- Protect Rules: 既定 **12 種**の ON/OFF + action（mask/redact/hash/replace）。
- Logs: メタデータ一覧（種別件数・レイテンシ・ステータス）。
- Playground: テキスト → マスク結果の即時プレビュー。

### ランタイム（Data Plane）
- `POST /v1/protect` — 検出・匿名化 → `maskedText`。
- `POST /v1/analyze` — マスク → Gemini → `analysis`（**フェイルクローズ**）。
- PII Engine: Presidio + GiNZA + JP Regex Recognizers（12 種）。
- 統一エラー / 構造化ログ / リクエスト ID。

### 対象 PII（12 種）
氏名・電話番号・メール・住所・郵便番号・URL・IP・銀行口座・クレジットカード・
マイナンバー・パスポート・法人番号。

## スコープ Out（MVP に含めない → 後続フェーズ）

| 項目 | フェーズ |
| --- | --- |
| Gemini 以外のプロバイダー（Claude/OpenAI/DeepSeek/Grok/Local） | Phase 3 |
| 組織メンバー招待・RBAC の本格運用 | Phase 3 |
| 可逆トークン化 Vault（永続再識別） | Phase 3 |
| Analytics の高度可視化・ロールアップ | Phase 2 |
| カスタム正規表現ルール UI | Phase 2 |
| レート制限・クォータ・課金 | Phase 2 |
| SDK（npm / pip） | Phase 2 |
| GraphQL / SSO / セルフホスト | Phase 4 |

## 受け入れ基準

MVP は以下をすべて満たすこと。

- [ ] サインアップ → プロジェクト作成 → Gemini 登録 → キー発行までを UI で完了できる。
- [ ] 発行した API キーで `POST /v1/protect` を呼ぶと、12 種の PII がマスクされて返る。
- [ ] `POST /v1/analyze` は、**マスク済みテキストのみ**が Gemini に送られ、分析結果が返る。
- [ ] 匿名化に失敗した場合、Analyze は LLM へ送信せず `502 ANONYMIZATION_FAILED` を返す（フェイルクローズ）。
- [ ] **生の PII・生テキストが DB／ログに保存されない**ことをレビューで確認。
- [ ] provider_keys が暗号化保存され、平文が API レスポンス/ログに出ない。
- [ ] SecureAI 発行キーは `key_hash` のみ保存され、平文は作成時 1 回のみ返る。
- [ ] Playground で任意テキストの検出・マスク結果を確認できる。
- [ ] Protect Rules の ON/OFF が Data Plane の挙動に反映される。
- [ ] エラー形式・ログ形式・requestId が全経路で統一されている。
- [ ] TypeScript strict / Python 型チェックが CI で緑。

## 成功指標（MVP 後の観測）

- 統合までの時間（Time to First Protected Request）: 15 分以内。
- Protect API p95 レイテンシ < 300ms（数 KB）。
- 主要 12 種 PII の検出再現率（社内テストコーパス）: 目標 95%+。
- 重大な PII 漏洩インシデント: 0 件。

## デモシナリオ（Exit 判定用）

1. サインアップして `demo` プロジェクトを作成。
2. Gemini プロバイダー + API キーを登録。
3. SecureAI API キーを発行（1回表示をコピー）。
4. Playground に「田中太郎 090-1234-5678 taro@example.com」を貼り、全てマスクされるのを確認。
5. cURL で `/v1/protect` と `/v1/analyze` を実行し、期待レスポンスを確認。
6. Logs に生 PII を含まないメタデータ行が記録されるのを確認。
