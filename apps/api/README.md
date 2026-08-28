# SecureAI Studio — API (FastAPI)

Data Plane: **Protect / Analyze / Detect**. Clean Architecture (domain →
application → infrastructure → api). See [design docs](../../docs/architecture/).

## セットアップ

```bash
cd apps/api
python3 -m venv .venv
.venv/bin/pip install -e .            # + optional: .[dev] / .[presidio]
cp .env.example .env
```

## 起動

```bash
.venv/bin/uvicorn src.main:app --reload   # http://localhost:8000  (docs: /docs)
```

`SECUREAI_DEV_SEED=true`（既定）で、以下がメモリに投入され即動作確認できます。

- dev プロジェクト + provider（既定 `echo` = 外部呼び出し不要）
- Protect キー: `SECUREAI_DEV_PROTECT_KEY`
- Analyze キー: `SECUREAI_DEV_ANALYZE_KEY`

## 動作確認

```bash
curl -X POST localhost:8000/v1/protect \
  -H "Authorization: Bearer sk_protect_dev_0000000000000000" \
  -H "Content-Type: application/json" \
  -d '{"text":"山田花子さんの email は taro@example.com","options":{"returnEntities":true}}'
```

## テスト

```bash
.venv/bin/pytest -q
```

## PII エンジン

- 既定は **Regex エンジン**（重い NLP 不要ですぐ動く）。パターン系 PII と
  Luhn / マイナンバー / 法人番号のチェックディジット検証を実装。
- `PERSON` / `LOCATION` の広い NER は `.[presidio]` を入れて **Presidio + GiNZA**
  バックエンドに差し替え可能（`PiiDetector` ポート）。
