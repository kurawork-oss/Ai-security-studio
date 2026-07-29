# ① システムアーキテクチャ

## 1. 全体像

SecureAI Studio は、責務の異なる **2 つの平面（Plane）** で構成します。
これにより、管理機能とリクエスト処理を独立してスケール・デプロイでき、
セキュリティ境界も明確になります。

- **Control Plane（管理平面）** — Studio ダッシュボード。プロジェクト / プロバイダー / キー / ルールの管理、ログ・分析の閲覧。
- **Data Plane（データ平面）** — Protect / Analyze API。実際に PII 検出・匿名化を行うランタイム経路。低レイテンシ・高スループットが要求される。

```mermaid
flowchart TB
    subgraph Client["クライアント"]
        Dev["開発者 / ユーザーシステム"]
        Browser["ブラウザ（管理者）"]
    end

    subgraph CP["Control Plane（管理平面）"]
        Web["Next.js Dashboard<br/>(App Router / RSC)"]
    end

    subgraph DP["Data Plane（データ平面）"]
        API["FastAPI Backend"]
        subgraph API_INNER[" "]
            direction TB
            MW["Auth / RateLimit<br/>Middleware"]
            PROT["Protect API"]
            ANALY["Analyze API"]
            PII["PII Engine<br/>(Presidio + GiNZA + Regex)"]
            PADAPT["Provider Adapter<br/>(Strategy)"]
        end
    end

    subgraph Data["データ層"]
        SB[("Supabase<br/>PostgreSQL + Auth")]
        SEC["Secrets / KMS<br/>(暗号化キー)"]
    end

    subgraph LLM["外部 LLM"]
        Gemini["Gemini API"]
        Others["Claude / OpenAI / ...（将来）"]
    end

    Browser --> Web
    Web -->|"Supabase Auth (JWT)"| SB
    Web -->|"REST /api/v1 (JWT)"| API
    Dev -->|"REST /v1 (API Key)"| API

    MW --> PROT --> PII
    MW --> ANALY --> PII
    ANALY --> PADAPT --> Gemini
    PADAPT -.-> Others
    API --> SB
    API --> SEC
    Web -.->|"設定取得"| SB
```

## 2. 主要コンポーネント

| コンポーネント | 責務 | 技術 |
| --- | --- | --- |
| **Web Dashboard** | 管理 UI。RSC でデータ取得、Client Component で対話。 | Next.js / shadcn/ui |
| **API Gateway (Middleware)** | 認証（JWT / API Key）、レート制限、リクエスト ID 付与、ロギング。 | FastAPI Middleware |
| **Protect API** | text を受け取り、PII を検出・匿名化して `maskedText` を返す。 | FastAPI |
| **Analyze API** | マスク後、登録済みプロバイダーへ送信し `analysis` を返す。 | FastAPI |
| **PII Engine** | 検出・匿名化の中核。多言語 NER + 日本語 NER + Regex。 | Presidio / GiNZA / Regex |
| **Provider Adapter** | LLM プロバイダー差異を吸収する抽象化層（Strategy Pattern）。 | Python |
| **Supabase** | データ永続化・認証・RLS。 | PostgreSQL |
| **Secrets/KMS** | プロバイダーキー等の暗号化。 | AES-256-GCM + KEK |

## 3. PII Engine の内部構成

Presidio を核に、日本語対応と JP 固有 PII のために GiNZA と Regex を組み合わせます。

```mermaid
flowchart LR
    IN["入力 text"] --> NORM["正規化<br/>(NFKC / 全半角)"]
    NORM --> ANALYZE["Presidio Analyzer"]
    subgraph Recognizers["Recognizer 群"]
        SPACY["spaCy/GiNZA NER<br/>(氏名・住所・組織)"]
        REGEX["Custom Regex Recognizers<br/>(電話/郵便/マイナンバー/法人番号/<br/>パスポート/口座/クレカ/IP/URL)"]
        BUILTIN["Presidio Builtin<br/>(EMAIL / CREDIT_CARD 等)"]
    end
    ANALYZE --> SPACY & REGEX & BUILTIN
    SPACY & REGEX & BUILTIN --> RESOLVE["重複解決 + 閾値フィルタ<br/>(score / allow・deny list)"]
    RESOLVE --> ANON["Presidio Anonymizer<br/>(mask / redact / hash / replace)"]
    ANON --> OUT["maskedText + entity metadata"]
```

- **Recognizer レジストリ** は Protect Rule（プロジェクト設定）で ON/OFF・スコア閾値を切り替え。
- **重複解決** — 複数 Recognizer が同一スパンを検出した場合、優先度・スコアで一意化。
- **クレジットカード** は Luhn チェック、**マイナンバー/法人番号** はチェックディジット検証で誤検出を抑制。

## 4. リクエストフロー

### 4.1 Protect API

```mermaid
sequenceDiagram
    participant C as ユーザーシステム
    participant M as Middleware
    participant P as Protect UseCase
    participant E as PII Engine
    participant D as DB(logs)
    C->>M: POST /v1/protect {text} + API Key
    M->>M: APIキー検証 / レート制限 / rule 解決
    M->>P: 認可済リクエスト
    P->>E: analyze + anonymize(text, rules)
    E-->>P: maskedText + entityCounts
    P->>D: メタデータのみ記録（生 PII は保存しない）
    P-->>C: 200 {maskedText, requestId}
```

### 4.2 Analyze API（フェイルクローズが重要）

```mermaid
sequenceDiagram
    participant C as ユーザーシステム
    participant M as Middleware
    participant A as Analyze UseCase
    participant E as PII Engine
    participant PR as Provider Adapter
    participant G as Gemini
    participant D as DB(logs)
    C->>M: POST /v1/analyze {text} + API Key
    M->>A: 認可済リクエスト
    A->>E: analyze + anonymize(text, rules)
    alt 匿名化に失敗
        E-->>A: error
        A-->>C: 502 {error} （★LLM へは送らない）
    else 匿名化に成功
        E-->>A: maskedText (+ 一時再識別マップ)
        A->>PR: complete(maskedText, providerKey)
        PR->>G: LLM リクエスト
        G-->>PR: 応答
        PR-->>A: analysis
        A->>A: （任意）再識別マップで復元
        A->>D: メタデータ + トークン使用量を記録
        A-->>C: 200 {analysis, requestId}
    end
```

## 5. 重要な設計判断

### 5.1 生 PII を永続化しない
Data Plane は PII を **通過させるだけ** で、DB には保存しません。
ログには「検出したエンティティ種別と件数」等のメタデータのみを記録します
（[セキュリティ設計](./09-security-design.md) 参照）。

### 5.2 匿名化のトークン戦略
- **既定: 不可逆プレースホルダ** — `<PERSON_1>`, `<EMAIL_2>` のように種別 + 連番。
- **可逆化（フェーズ2）** — Analyze で応答に実データを戻したい場合のため、
  リクエスト処理中のみ有効な **一時マップ** を保持（メモリ内、永続化なし）。
  恒久的な可逆化が必要なら、別途トークン Vault を導入（`D-2`）。

### 5.3 Provider Adapter による拡張
LLM プロバイダーは `ProviderAdapter` インターフェース（port）で抽象化し、
Gemini 実装から着手。Claude / OpenAI / DeepSeek / Grok / Local は同一 IF で追加します。
これは [SOLID の OCP] と [Strategy Pattern] に基づきます。

### 5.4 Control Plane と Data Plane の分離
両者は同一 FastAPI アプリ内のルーター分割で開始し（MVP）、
負荷特性が乖離したらデプロイ単位を分割できるようコード境界を明確化します。

## 6. 非機能要件（目標値・初期）

| 項目 | 目標 |
| --- | --- |
| Protect API レイテンシ | p95 < 300ms（数 KB のテキスト） |
| 可用性 | 99.9%（データ平面） |
| データ保持 | 生 PII: 0（永続化しない） / ログメタデータ: 既定 90 日 |
| スケール | ステートレス水平スケール（PII Engine はワーカープール） |
