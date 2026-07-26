"""Unit tests for admin utilities (passwords, settings parsing, directories)."""

from __future__ import annotations

import pytest

from app.admin.models.enums import SettingType
from app.admin.services.directory_service import (
    DIRECTORIES,
    editable_columns,
)
from app.admin.services.settings_service import parse_value
from app.admin.utils.passwords import (
    PasswordRules,
    hash_password,
    validate_password,
    verify_password,
)
from app.core.exceptions import ValidationError


def test_password_hash_roundtrip() -> None:
    encoded = hash_password("S3cretPass")
    assert encoded.startswith("pbkdf2_sha256$")
    assert verify_password("S3cretPass", encoded) is True
    assert verify_password("wrong", encoded) is False


def test_password_hash_is_salted() -> None:
    assert hash_password("same") != hash_password("same")


def test_validate_password_rules() -> None:
    rules = PasswordRules(min_length=8)
    assert validate_password("Ab1cdefg", rules) == []
    problems = validate_password("abc", rules)
    assert any("длина" in p for p in problems)
    assert any("заглавная" in p for p in problems)
    assert any("цифра" in p for p in problems)


def test_validate_password_special_required() -> None:
    rules = PasswordRules(require_special=True)
    assert validate_password("Abcdef12", rules) == ["нужен специальный символ"]
    assert validate_password("Abcdef12!", rules) == []


def test_parse_value_types() -> None:
    assert parse_value("42", SettingType.INTEGER) == 42
    assert parse_value("1.5", SettingType.NUMBER) == 1.5
    assert parse_value("true", SettingType.BOOLEAN) is True
    assert parse_value("off", SettingType.BOOLEAN) is False
    assert parse_value('{"a": 1}', SettingType.JSON) == {"a": 1}
    assert parse_value("hello", SettingType.STRING) == "hello"
    assert parse_value(None, SettingType.STRING) is None


def test_parse_value_invalid_raises() -> None:
    with pytest.raises(ValidationError):
        parse_value("notanint", SettingType.INTEGER)
    with pytest.raises(ValidationError):
        parse_value("{bad json", SettingType.JSON)


def test_directory_registry_and_columns() -> None:
    assert "resource_types" in DIRECTORIES
    assert "organizations" in DIRECTORIES
    model, _label = DIRECTORIES["resource_types"]
    cols = editable_columns(model)
    assert "category" in cols
    # base columns are excluded
    assert "code" not in cols and "id" not in cols
    org_model, _ = DIRECTORIES["organizations"]
    org_cols = editable_columns(org_model)
    assert "phone" in org_cols and "email" in org_cols
