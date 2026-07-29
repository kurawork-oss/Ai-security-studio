# ⑥ UI 設計

## デザイン原則

- **Google AI Studio 風** — 落ち着いた中立色、広い余白、コンテンツ主役、開発者向けの密度。
- **一貫性** — shadcn/ui（Radix ベース）+ Tailwind のトークンで統一。
- **アクセシビリティ** — WCAG AA、キーボード操作、フォーカスリング、`aria-*`。
- **ライト/ダーク両対応** — CSS 変数で切替。既定はシステム追従。

## レイアウト

```text
┌───────────────────────────────────────────────────────────┐
│ Topbar:  [☰] SecureAI Studio    [Project ▾]     [🔔][User▾]│
├───────────┬───────────────────────────────────────────────┤
│ Sidebar   │  Page Header (title + primary action)         │
│           │  ┌─────────────────────────────────────────┐  │
│ Dashboard │  │  Content                                │  │
│ Projects  │  │  (Cards / Table / Form / Charts)        │  │
│ Providers │  │                                         │  │
│ API Keys  │  └─────────────────────────────────────────┘  │
│ ...       │                                               │
│ [User ▾]  │                                               │
└───────────┴───────────────────────────────────────────────┘
```

- サイドバーは折りたたみ可能（アイコンのみ）。モバイルは Sheet でオフキャンバス表示。
- Page Header は「タイトル + 説明 + 主要 CTA（右上）」で全画面統一。

## デザイントークン（例）

CSS 変数（`globals.css`）で定義し、Tailwind から参照。**色はハードコードしない**。

| トークン | 用途 | 例（light / dark） |
| --- | --- | --- |
| `--background` / `--foreground` | 背景 / 文字 | `#ffffff` / `#0b0f14` |
| `--primary` | 主要アクション | 落ち着いた青系 |
| `--muted` / `--muted-foreground` | 補助・キャプション | グレー系 |
| `--destructive` | 破壊操作 | 赤系 |
| `--border` / `--ring` | 罫線 / フォーカス | 低コントラスト |
| radius | 角丸 | `0.5rem` 基準 |

タイポグラフィ: 本文 `Inter` 系、コード `JetBrains Mono` 系（`next/font` でセルフホスト）。

## コンポーネント在庫（shadcn/ui）

| カテゴリ | コンポーネント |
| --- | --- |
| 入力 | Button, Input, Textarea, Select, Switch, Checkbox, Form(+ react-hook-form + zod) |
| 表示 | Card, Table, Badge, Avatar, Tabs, Tooltip, Separator, Skeleton |
| オーバーレイ | Dialog, Sheet, Popover, Dropdown Menu, Command(⌘K パレット) |
| フィードバック | Toast(sonner), Alert, Progress |
| データ | Chart(recharts ラッパ), DataTable(TanStack Table) |

## 画面別 UI の要点

### Dashboard
- 上段に KPI カード（今日のリクエスト数 / 検出 PII 件数 / エラー率 / p95 レイテンシ）。
- 折れ線（リクエスト推移）+ 直近アクティビティ + 「クイックスタート」チェックリスト。

### Protect Rules（重要 UX）
- カテゴリ（identity / contact / financial / network / gov_id）ごとにグルーピング。
- 各ルールは **Switch（ON/OFF）+ Action セレクト（mask/redact/hash/replace）+ 詳細（閾値・許可/拒否）**。
- 上部に「＋ カスタムルール追加」（正規表現 + ラベル + action）。
- 変更は下部固定バーで **一括保存（Save changes / Discard）**。

```text
Contact ───────────────────────────────
  [●] Email        action:[mask ▾]   ⚙
  [●] Phone number action:[redact ▾] ⚙
Gov ID ────────────────────────────────
  [●] マイナンバー  action:[hash ▾]   ⚙
  [ ] パスポート    action:[mask ▾]   ⚙
                          [＋ カスタムルール]
──────────────────────────────────────
        変更あり  [ Discard ] [ Save changes ]
```

### Protect Playground（差別化の中核体験）
- 左右分割: 入力テキスト／保護後プレビュー（`[PERSON]`・`[PHONE]` を**色分けハイライト**＋対応表）。
- 上部にルールのクイックトグル・Provider 選択・「保護実行」「Gemini で分析」ボタン。
- 「検出件数 / マスク率 / 種別内訳」の統計、下部に **再現用 cURL / SDK スニペット**（コピー）。
- サンプルデータ投入。貼付テキストは**永続化しない**。詳細は [Protect Playground 設計](./15-protect-playground.md)。

### Export
- ターゲット（Claude Code / Codex / Cursor / Windsurf）と言語（TS/Python）を選択 → プロンプト生成 → コピー。
- 生成物に**実キーを含めず**環境変数プレースホルダを表示（[Export Module](./13-export-module.md)）。

### API Keys（Protect / Analyze 分離）
- 上部に **Protect / Analyze のタブ**。用途ごとにキーを一覧・発行。
- 発行モーダルは **1回だけ平文表示** + コピー + 「もう表示されません」の警告。プレフィックスで用途が判別可能（`sk_protect_`/`sk_analyze_`）。
- テーブルは `keyPrefix`・用途・最終利用・状態。行から **ローテーション**（新旧併存の猶予表示）・失効。

### Providers
- 登録: provider_type 選択（Gemini を既定強調、他は "Coming soon" バッジ）。
- 詳細でキー登録（入力後は末尾4桁のみ表示）・ローテーション・既定モデル設定。

### Logs / Analytics
- Logs: DataTable（endpoint / status / latency / entity_counts / time）+ フィルタ + requestId 検索。
- Analytics: 期間セレクタ + 時系列（リクエスト数・**Protect 件数**・応答時間 p95）+ **PII 種別内訳**（ドーナツ）+ **Provider 利用率** + **Token 数** + エラー率。

## 状態・空状態・エラー

- **Empty State** — 各一覧は「まだありません + 作成 CTA + 短い説明」を必ず用意。
- **Loading** — Skeleton を使用（レイアウトシフト回避）。
- **Error** — 統一エラーカード（`requestId` 表示 + 再試行）。Toast で操作結果を通知。

## レスポンシブ

- `md` 未満: サイドバーを Sheet 化、テーブルは横スクロール or カード化。
- チャート・コードブロックは `overflow-x-auto` のコンテナ内でスクロール。
