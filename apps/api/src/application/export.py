"""Export module — generate ready-to-paste integration prompts for AI coding
tools (Claude Code / Codex / Cursor / Windsurf).

Generated content NEVER contains a real API key — only an environment-variable
placeholder (see docs/architecture/13-export-module.md).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..core.errors import ValidationError

TARGET_META = [
    {"id": "claude_code", "label": "Claude Code"},
    {"id": "codex", "label": "Codex"},
    {"id": "cursor", "label": "Cursor"},
    {"id": "windsurf", "label": "Windsurf"},
]
_TARGET_IDS = {t["id"] for t in TARGET_META}
_TARGET_LABEL = {t["id"]: t["label"] for t in TARGET_META}


@dataclass(frozen=True)
class ExportContext:
    pattern: str            # "protect" | "analyze"
    language: str           # "typescript" | "python" | ...
    api_base_url: str
    enabled_rules: list[str]
    key_env_var: str        # e.g. SECUREAI_PROTECT_KEY (value never included)
    provider_type: str | None = None


@dataclass(frozen=True)
class ExportArtifact:
    target_id: str
    title: str
    content: str
    format: str = "markdown"


def render(target_id: str, ctx: ExportContext) -> ExportArtifact:
    if target_id not in _TARGET_IDS:
        raise ValidationError(
            f"Unknown export target '{target_id}'",
            details={"targets": sorted(_TARGET_IDS)},
        )
    if ctx.pattern not in {"protect", "analyze"}:
        raise ValidationError("pattern must be 'protect' or 'analyze'")

    label = _TARGET_LABEL[target_id]
    endpoint = f"/v1/{ctx.pattern}"
    rules = ", ".join(ctx.enabled_rules) or "(none enabled)"
    output_field = "maskedText" if ctx.pattern == "protect" else "analysis"
    title = f"SecureAI {ctx.pattern} 統合（{label} / {ctx.language}）"

    content = f"""# タスク: SecureAI を {ctx.language} コードに統合する（{label} 向け）

あなたは既存の {ctx.language} コードに SecureAI Studio の **{ctx.pattern} API** を組み込みます。
LLM へデータを送る前に、必ず SecureAI を通して PII を保護してください。

## 制約
- API キーは環境変数 `{ctx.key_env_var}` から読み込み、**ハードコードしない**。
- 生の個人情報をログに残さない。

## 呼び出し仕様
- Endpoint: `POST {ctx.api_base_url}{endpoint}`
- Header: `Authorization: Bearer ${{{ctx.key_env_var}}}`
- Request body: `{{ "text": "<ユーザー入力>" }}`
- Response から `{output_field}` を取得して利用する。
"""
    if ctx.pattern == "protect":
        content += "- 取得した `maskedText` のみを、後段の LLM 呼び出しへ渡すこと。\n"
    else:
        provider = ctx.provider_type or "登録済みプロバイダー"
        content += f"- SecureAI が {provider} を呼び出し、`analysis` を返します。\n"

    content += f"""
## 保護対象（有効な PII 種別）
{rules}

上記に沿って、統合用の関数と最小テストを生成してください。"""

    return ExportArtifact(target_id=target_id, title=title, content=content)
