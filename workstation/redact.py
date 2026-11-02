"""Redaction of credentials, private prompts and personal paths (R1, shared).

Used by recipe export, reproduction manifests and copied diagnostics.
Planned: #15.
"""

REDACTED = "[redacted]"
PRIVATE = "[private]"

SECRET_KEYS = frozenset({
    "api_key", "apikey", "token", "access_token", "hf_token",
    "password", "secret", "authorization",
})
PRIVATE_KEYS = frozenset({"prompt", "prompts", "messages", "private_prompt", "system_prompt"})


def redact(obj, *, home_dirs=()):
    """Return a redacted deep copy of ``obj``; never mutate it. See the issue brief."""
    raise NotImplementedError("TODO #15")
