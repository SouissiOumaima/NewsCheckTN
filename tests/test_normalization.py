"""Tests Lot A2."""

from common.schemas import Lang
from normalization.normalize import detect_language, normalize, normalize_arabic


def test_detect_language_fr():
    assert detect_language("Le gouvernement a annoncé une hausse.") == Lang.FR


def test_detect_language_ar():
    assert detect_language("أعلنت الحكومة عن زيادة") == Lang.AR


def test_detect_language_arabizi():
    assert detect_language("3lech el 7koma ma 9alet chay") == Lang.TN


def test_normalize_arabic_removes_diacritics():
    assert normalize_arabic("مَدْرَسَة") == "مدرسه"


def test_normalize_whitespace():
    assert normalize("  Bonjour   Tunis  ").text == "Bonjour Tunis"
