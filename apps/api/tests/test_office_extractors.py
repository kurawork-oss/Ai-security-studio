"""Tests for optional office extractors (docx/xlsx). Skipped if libs absent."""

from __future__ import annotations

import base64
import io

import pytest

from tests.conftest import PROTECT_KEY, auth

docx = pytest.importorskip("docx")
openpyxl = pytest.importorskip("openpyxl")

from src.infrastructure.plugins.office_extractors import DocxExtractor, XlsxExtractor  # noqa: E402

DOCX_CT = DocxExtractor.manifest.content_types[0]
XLSX_CT = XlsxExtractor.manifest.content_types[0]


def make_docx(text: str) -> bytes:
    d = docx.Document()
    d.add_paragraph(text)
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


def make_xlsx(rows: list[list[str]]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_docx_extract_unit():
    text = DocxExtractor().extract(make_docx("連絡は taro@example.com"), DOCX_CT)
    assert "taro@example.com" in text


def test_xlsx_extract_unit():
    content = make_xlsx([["name", "email"], ["田中", "taro@example.com"]])
    assert "taro@example.com" in XlsxExtractor().extract(content, XLSX_CT)


def test_extract_api_masks_docx(client):
    b64 = base64.b64encode(make_docx("連絡は taro@example.com")).decode("ascii")
    r = client.post(
        "/v1/extract",
        json={"contentType": DOCX_CT, "contentBase64": b64},
        headers=auth(PROTECT_KEY),
    )
    assert r.status_code == 200
    masked = r.json()["maskedText"]
    assert "taro@example.com" not in masked and "<EMAIL_ADDRESS_1>" in masked


def test_office_plugins_available(client):
    plugins = {p["key"]: p for p in client.get("/v1/plugins").json()}
    assert plugins["docx"]["available"] is True
    assert plugins["xlsx"]["available"] is True
    assert plugins["pdf"]["available"] is True
