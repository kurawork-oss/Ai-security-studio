"""Content-extractor plugins (stdlib only).

Turn common structured/markup content into plain text so the PII engine can
scan it. Heavy formats (PDF/DOCX/XLSX/OCR/Audio) are declared as stubs in
``builtin`` and enabled by installing the corresponding optional plugin.
"""

from __future__ import annotations

import csv
import io
import json
from html.parser import HTMLParser

from ...core.errors import ValidationError
from ...domain.plugins import PluginManifest


def _decode(content: bytes) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationError("Content is not valid UTF-8") from exc


class PlaintextExtractor:
    manifest = PluginManifest(
        key="plaintext",
        category="extractor",
        description="Plain text / Markdown passthrough",
        content_types=("text/plain", "text/markdown"),
    )

    def supports(self, content_type: str) -> bool:
        return content_type in self.manifest.content_types

    def extract(self, content: bytes, content_type: str) -> str:
        return _decode(content)


class CsvExtractor:
    manifest = PluginManifest(
        key="csv",
        category="extractor",
        description="CSV/TSV to text",
        content_types=("text/csv", "text/tab-separated-values"),
    )

    def supports(self, content_type: str) -> bool:
        return content_type in self.manifest.content_types

    def extract(self, content: bytes, content_type: str) -> str:
        delimiter = "\t" if content_type.endswith("tab-separated-values") else ","
        reader = csv.reader(io.StringIO(_decode(content)), delimiter=delimiter)
        return "\n".join(" ".join(cell for cell in row) for row in reader)


class JsonExtractor:
    manifest = PluginManifest(
        key="json",
        category="extractor",
        description="JSON scalar values to text",
        content_types=("application/json",),
    )

    def supports(self, content_type: str) -> bool:
        return content_type in self.manifest.content_types

    def extract(self, content: bytes, content_type: str) -> str:
        try:
            data = json.loads(_decode(content))
        except json.JSONDecodeError as exc:
            raise ValidationError("Invalid JSON content") from exc
        values: list[str] = []
        self._collect(data, values)
        return "\n".join(values)

    def _collect(self, node: object, out: list[str]) -> None:
        if isinstance(node, str):
            out.append(node)
        elif isinstance(node, (int, float)) and not isinstance(node, bool):
            out.append(str(node))
        elif isinstance(node, dict):
            for v in node.values():
                self._collect(v, out)
        elif isinstance(node, list):
            for v in node:
                self._collect(v, out)


class _TextHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in {"script", "style"}:
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"}:
            self._skip = False

    def handle_data(self, data: str) -> None:
        if not self._skip and data.strip():
            self.parts.append(data.strip())


class HtmlExtractor:
    manifest = PluginManifest(
        key="html",
        category="extractor",
        description="HTML to visible text",
        content_types=("text/html",),
    )

    def supports(self, content_type: str) -> bool:
        return content_type in self.manifest.content_types

    def extract(self, content: bytes, content_type: str) -> str:
        parser = _TextHtmlParser()
        parser.feed(_decode(content))
        return "\n".join(parser.parts)


# Declared-but-not-yet-implemented plugins (need system deps or a vector store).
STUB_MANIFESTS = [
    PluginManifest("ocr-image", "extractor", description="OCR (needs tesseract)",
                   content_types=("image/png", "image/jpeg"), available=False),
    PluginManifest("audio-transcribe", "extractor", description="Audio (needs whisper)",
                   content_types=("audio/wav", "audio/mpeg"), available=False),
    PluginManifest("rag", "augmentation", description="Retrieval augmentation", available=False),
    PluginManifest("streaming", "delivery", description="Streaming responses"),
    PluginManifest("batch-analyze", "delivery", description="Batch analyze"),
    PluginManifest("mcp", "protocol", description="Expose Protect/Analyze as MCP tools",
                   available=False),
]


def register_builtin_plugins(registry) -> None:
    from .office_extractors import available_office_extractors, missing_office_manifests

    for extractor in (PlaintextExtractor(), CsvExtractor(), JsonExtractor(), HtmlExtractor()):
        registry.register_extractor(extractor)
    # PDF/Word/Excel are available when their optional libs are installed.
    for extractor in available_office_extractors():
        registry.register_extractor(extractor)
    for manifest in missing_office_manifests():
        registry.register_manifest(manifest)
    # webhook delivery is a real plugin; registered by the container separately.
    for manifest in STUB_MANIFESTS:
        registry.register_manifest(manifest)
