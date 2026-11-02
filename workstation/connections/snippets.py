"""Copyable client settings with no secrets in them (M3)."""

import json
from urllib.parse import urlsplit, urlunsplit


def client_snippets(base_url: str, model: str, *, api_key_env: str = "OPENAI_API_KEY") -> dict:
    """Return environment, curl, and Python settings for an OpenAI-compatible API."""
    parsed = urlsplit(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("base_url must be an http or https URL")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("base_url must not contain credentials")

    path = parsed.path.rstrip("/")
    if not path.endswith("/v1"):
        path += "/v1"
    base = urlunsplit((parsed.scheme, parsed.netloc, path, parsed.query, parsed.fragment))

    if not model or any(char.isspace() or char in "'\\\"" for char in model):
        raise ValueError("model must not be empty or contain quotes, backslashes, or whitespace")

    body = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": "Say hello"}],
            "max_tokens": 16,
        }
    )
    return {
        "env": f"export OPENAI_BASE_URL={base}\nexport OPENAI_MODEL={model}\n",
        "curl": (
            f"curl {base}/chat/completions \\\n"
            '  -H "Content-Type: application/json" \\\n'
            f'  -H "Authorization: Bearer ${api_key_env}" \\\n'
            f"  -d '{body}'\n"
        ),
        "python": (
            "import os\nfrom openai import OpenAI\n\n"
            f'client = OpenAI(base_url="{base}", '
            f'api_key=os.environ.get("{api_key_env}", "none"))\n'
            f'reply = client.chat.completions.create(model="{model}", '
            'messages=[{"role": "user", "content": "Say hello"}], max_tokens=16)\n'
            "print(reply.choices[0].message.content)\n"
        ),
    }
