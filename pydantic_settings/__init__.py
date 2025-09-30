"""Minimal fallback implementation of :mod:`pydantic_settings` for tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar, Dict

from pydantic import BaseModel


class BaseSettings(BaseModel):
    """Simplified stand-in for :class:`pydantic_settings.BaseSettings`."""

    model_config: ClassVar[Dict[str, Any]] = {}

    def __init__(self, **data: Any) -> None:
        env_values = self._load_env_file()
        env_values.update(self._load_env_vars())
        env_values.update(data)
        super().__init__(**env_values)

    @classmethod
    def _load_env_vars(cls) -> Dict[str, Any]:
        from os import environ

        values: Dict[str, Any] = {}
        for field_name in cls.model_fields:
            env_key = field_name.upper()
            if env_key in environ:
                values[field_name] = environ[env_key]
        return values

    @classmethod
    def _load_env_file(cls) -> Dict[str, Any]:
        env_file = getattr(getattr(cls, "Config", object), "env_file", None)
        if not env_file:
            return {}

        path = Path(env_file)
        if not path.exists():
            return {}

        values: Dict[str, Any] = {}
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.lower()] = value
        return values

