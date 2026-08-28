-- SecureAI Studio — seed data (idempotent)
-- Builtin PII catalog, plugin catalog, and global export templates.

-- ── 12 default PII entity types (org_id NULL = builtin/global) ──
insert into public.pii_entity_types (code, label, category, is_builtin) values
    ('PERSON',              '氏名',             'identity',  true),
    ('PHONE_NUMBER',        '電話番号',         'contact',   true),
    ('EMAIL_ADDRESS',       'メール',           'contact',   true),
    ('LOCATION',            '住所',             'identity',  true),
    ('JP_POSTAL_CODE',      '郵便番号',         'contact',   true),
    ('URL',                 'URL',              'network',   true),
    ('IP_ADDRESS',          'IP',               'network',   true),
    ('JP_BANK_ACCOUNT',     '銀行口座',         'financial', true),
    ('CREDIT_CARD',         'クレジットカード', 'financial', true),
    ('JP_MYNUMBER',         'マイナンバー',     'gov_id',    true),
    ('JP_PASSPORT',         'パスポート',       'gov_id',    true),
    ('JP_CORPORATE_NUMBER', '法人番号',         'gov_id',    true)
on conflict (code) do nothing;

-- ── Plugin catalog (future capabilities, provisioned) ──
insert into public.plugins (plugin_key, category, is_builtin) values
    ('pdf-extractor',    'extractor',    true),
    ('docx-extractor',   'extractor',    true),
    ('xlsx-extractor',   'extractor',    true),
    ('ocr-image',        'extractor',    true),
    ('audio-transcribe', 'extractor',    true),
    ('rag',              'augmentation', true),
    ('webhook',          'delivery',     true),
    ('streaming',        'delivery',     true),
    ('batch-analyze',    'delivery',     true),
    ('mcp',              'protocol',     true)
on conflict (plugin_key) do nothing;

-- ── Global export templates (project_id NULL = builtin) ──
insert into public.export_templates (project_id, target_id, language, body, is_builtin)
select null, 'claude_code', 'typescript',
$tmpl$# タスク: SecureAI Protect を統合する

LLM へ送信する前段として SecureAI Protect API を組み込んでください。
API キーは環境変数 `SECUREAI_PROTECT_KEY` から読み込み、ハードコードしないこと。

- エンドポイント: POST {{api_base_url}}/v1/protect
- 入力: { "text": "<ユーザー入力>" }
- 出力: { "maskedText": "..." } を取得し、以降の LLM 呼び出しには maskedText のみを渡す

統合コードと最小テストを生成してください。$tmpl$,
    true
where not exists (
    select 1 from public.export_templates
    where is_builtin and target_id = 'claude_code' and language = 'typescript'
);
