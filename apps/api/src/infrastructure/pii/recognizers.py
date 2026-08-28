"""Recognizers for the built-in PII entity types.

Pattern-based entities (email, phone, postal, URL, IP, card, My Number,
Corporate Number, passport) are matched by regex + validators and are reliable.

PERSON / LOCATION / BANK_ACCOUNT use lightweight heuristics (honorific,
prefecture-anchored address, contextual keywords) plus an optional name
gazetteer. Broad, context-free coverage of these is the job of the optional
Presidio + GiNZA backend (see PresidioPiiDetector); the regex engine keeps the
MVP runnable without heavyweight NLP models.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from ...domain.value_objects import BuiltinEntity
from . import validators as v

PREFECTURES = (
    "北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|"
    "千葉県|東京都|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|"
    "愛知県|三重県|滋賀県|京都府|大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|"
    "広島県|山口県|徳島県|香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|"
    "宮崎県|鹿児島県|沖縄県"
)


@dataclass(frozen=True)
class Recognizer:
    entity_type: str
    regex: re.Pattern[str]
    score: float
    group: int = 0
    validator: Callable[[str], bool] | None = None


def builtin_recognizers(gazetteer: list[str] | None = None) -> list[Recognizer]:
    recs: list[Recognizer] = [
        Recognizer(
            BuiltinEntity.EMAIL_ADDRESS,
            re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"),
            0.95,
        ),
        Recognizer(
            BuiltinEntity.URL,
            re.compile(r"https?://[^\s<>\"'））」]+"),
            0.9,
        ),
        Recognizer(
            BuiltinEntity.IP_ADDRESS,
            re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])"),
            0.9,
            validator=v.ipv4_valid,
        ),
        # Credit card: 13–19 digits with optional spaces/hyphens, Luhn-checked.
        Recognizer(
            BuiltinEntity.CREDIT_CARD,
            re.compile(r"(?<!\d)\d(?:[ \-]?\d){12,18}(?!\d)"),
            0.95,
            validator=v.luhn_valid,
        ),
        # Corporate Number: 13 digits + check digit.
        Recognizer(
            BuiltinEntity.JP_CORPORATE_NUMBER,
            re.compile(r"(?<!\d)\d{13}(?!\d)"),
            0.9,
            validator=v.corporate_number_valid,
        ),
        # My Number: 12 digits (optionally grouped) + check digit.
        Recognizer(
            BuiltinEntity.JP_MYNUMBER,
            re.compile(r"(?<!\d)\d{4}[ \-]?\d{4}[ \-]?\d{4}(?!\d)"),
            0.9,
            validator=v.mynumber_valid,
        ),
        # Mobile / +81 / hyphenated landline.
        Recognizer(
            BuiltinEntity.PHONE_NUMBER,
            re.compile(
                r"(?<![\d\-])(?:"
                r"0[789]0[\-\s]?\d{4}[\-\s]?\d{4}"
                r"|\+81[\-\s]?\d{1,4}[\-\s]?\d{1,4}[\-\s]?\d{3,4}"
                r"|0\d{1,3}[\-\s]\d{1,4}[\-\s]\d{3,4}"
                r")(?![\d\-])"
            ),
            0.8,
        ),
        Recognizer(
            BuiltinEntity.JP_POSTAL_CODE,
            re.compile(r"〒?\s?(?<!\d)\d{3}-\d{4}(?!\d)"),
            0.75,
        ),
        Recognizer(
            BuiltinEntity.JP_PASSPORT,
            re.compile(r"(?<![A-Z0-9])[A-Z]{2}\d{7}(?![A-Z0-9])"),
            0.7,
        ),
        # Bank account: 7 digits near an account keyword (contextual).
        Recognizer(
            BuiltinEntity.JP_BANK_ACCOUNT,
            re.compile(r"(?:口座番号|口座|普通預金|普通|当座)[^\d]{0,8}(\d{7})(?!\d)"),
            0.6,
            group=1,
        ),
        # Address: prefecture-anchored heuristic.
        Recognizer(
            BuiltinEntity.LOCATION,
            re.compile(rf"(?:{PREFECTURES})[^\s、。，,]{{0,25}}"),
            0.6,
        ),
        # Person: name (kanji / katakana) immediately followed by a Japanese
        # honorific. Hiragana is excluded so trailing particles (は/の/が…) are
        # not swallowed into the name. Broad NER is the GiNZA backend's job.
        Recognizer(
            BuiltinEntity.PERSON,
            re.compile(r"([一-龥々〆ヶァ-ヴー]{2,8})(?=さん|様|氏|くん|君|ちゃん|殿)"),
            0.6,
            group=1,
        ),
    ]

    if gazetteer:
        names = sorted({n for n in gazetteer if n}, key=len, reverse=True)
        if names:
            pattern = "|".join(re.escape(n) for n in names)
            recs.append(
                Recognizer(BuiltinEntity.PERSON, re.compile(pattern), 0.9)
            )
    return recs
