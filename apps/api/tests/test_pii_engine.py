"""Unit tests for the PII engine: validators, detection, anonymization."""

from __future__ import annotations

from src.domain.services import Anonymizer, deanonymize
from src.domain.value_objects import BuiltinEntity
from src.infrastructure.pii import validators as v
from src.infrastructure.pii.regex_detector import RegexPiiDetector
from src.infrastructure.repositories.memory import default_rules


def types(spans):
    return {s.entity_type for s in spans}


def test_validators():
    assert v.luhn_valid("4242 4242 4242 4242")
    assert not v.luhn_valid("4242424242424241")
    assert v.mynumber_valid("123456789018")
    assert not v.mynumber_valid("123456789012")
    assert v.corporate_number_valid("7010001064648")  # NTT
    assert not v.corporate_number_valid("1234567890123")
    assert v.ipv4_valid("192.168.0.1")
    assert not v.ipv4_valid("999.1.1.1")


def test_detects_pattern_entities():
    detector = RegexPiiDetector()
    text = (
        "連絡先は taro@example.com、電話 090-1234-5678、"
        "カードは 4242 4242 4242 4242、法人番号 7010001064648、"
        "個人番号 123456789018、住所 東京都千代田区1-1、〒100-0001"
    )
    found = types(detector.detect(text, default_rules()))
    assert BuiltinEntity.EMAIL_ADDRESS in found
    assert BuiltinEntity.PHONE_NUMBER in found
    assert BuiltinEntity.CREDIT_CARD in found
    assert BuiltinEntity.JP_CORPORATE_NUMBER in found
    assert BuiltinEntity.JP_MYNUMBER in found
    assert BuiltinEntity.JP_POSTAL_CODE in found
    assert BuiltinEntity.LOCATION in found


def test_person_honorific_heuristic():
    detector = RegexPiiDetector()
    spans = detector.detect("担当は山田花子さんです", default_rules())
    person = [s for s in spans if s.entity_type == BuiltinEntity.PERSON]
    assert person and person[0].text == "山田花子"


def test_invalid_mynumber_not_detected():
    detector = RegexPiiDetector()
    # 12 digits but failing the check digit -> must not be flagged as My Number.
    spans = detector.detect("番号 123456789012 は無効", default_rules())
    assert BuiltinEntity.JP_MYNUMBER not in types(spans)


def test_anonymize_and_deanonymize_roundtrip():
    detector = RegexPiiDetector()
    anonymizer = Anonymizer()
    text = "taro@example.com に送って、taro@example.com にも"
    result = anonymizer.anonymize(text, detector.detect(text, default_rules()), default_rules())

    assert "taro@example.com" not in result.masked_text
    assert "<EMAIL_ADDRESS_1>" in result.masked_text
    # Same value reused -> same placeholder (deterministic within a request).
    assert result.masked_text.count("<EMAIL_ADDRESS_1>") == 2
    assert result.entity_counts[BuiltinEntity.EMAIL_ADDRESS] == 1
    # Round trip restores the original.
    assert deanonymize(result.masked_text, result.mapping) == text


def test_disabled_rule_is_not_detected():
    detector = RegexPiiDetector()
    rules = [r for r in default_rules() if r.entity_type != BuiltinEntity.EMAIL_ADDRESS]
    spans = detector.detect("taro@example.com", rules)
    assert BuiltinEntity.EMAIL_ADDRESS not in types(spans)
