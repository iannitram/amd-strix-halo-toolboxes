"""Redaction of credentials, private prompts and personal paths (R1, shared).

Used by recipe export, reproduction manifests and copied diagnostics.
Planned: #15.
"""

import re

REDACTED = "[redacted]"
PRIVATE = "[private]"

SECRET_KEYS = frozenset({
    "api_key", "apikey", "token", "access_token", "hf_token",
    "password", "secret", "authorization",
})
PRIVATE_KEYS = frozenset({"prompt", "prompts", "messages", "private_prompt", "system_prompt"})

_UNIX_HOME = re.compile(r"(?<![A-Za-z0-9_./~-])(?:/home|/var/home|/Users)/[^/\\\s\"'<>|]+")
_WINDOWS_HOME = re.compile(r"(?<![A-Za-z0-9_])([A-Za-z]:\\Users\\)[^\\/\s\"'<>|]+", re.IGNORECASE)


def _redact_string(value, home_dirs):
    for home_dir in home_dirs:
        value = value.replace(home_dir, "~")
    value = _UNIX_HOME.sub("~", value)
    return _WINDOWS_HOME.sub("~", value)


def redact(obj, *, home_dirs=()):
    """Return a redacted deep copy of ``obj``; never mutate it. See the issue brief."""
    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            normalized = key.lower().replace("-", "_") if isinstance(key, str) else None
            if normalized in SECRET_KEYS:
                result[key] = REDACTED
            elif normalized in PRIVATE_KEYS:
                result[key] = PRIVATE
            else:
                result[key] = redact(value, home_dirs=home_dirs)
        return result
    if isinstance(obj, (list, tuple)):
        return [redact(value, home_dirs=home_dirs) for value in obj]
    if isinstance(obj, str):
        return _redact_string(obj, home_dirs)
    return obj
