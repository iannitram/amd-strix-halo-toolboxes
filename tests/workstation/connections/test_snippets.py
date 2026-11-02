"""Locked tests for #43 (workstation/connections/snippets.py). One test per Expectation sentence."""

import pytest

from workstation.connections.snippets import client_snippets

BODY = ('{"model": "qwen3-30b", "messages": [{"role": "user", "content": "Say hello"}], '
        '"max_tokens": 16}')


def test_e1_base_url_normalised():
    for url in ("http://127.0.0.1:8080", "http://127.0.0.1:8080/", "http://127.0.0.1:8080/v1",
                "http://127.0.0.1:8080/v1/"):
        env = client_snippets(url, "qwen3-30b")["env"]
        assert env.startswith("export OPENAI_BASE_URL=http://127.0.0.1:8080/v1\n")


def test_e2_bad_inputs():
    with pytest.raises(ValueError):
        client_snippets("127.0.0.1:8080", "m")
    with pytest.raises(ValueError):
        client_snippets("ftp://host/", "m")
    with pytest.raises(ValueError, match="^base_url must not contain credentials$"):
        client_snippets("http://me:pw@127.0.0.1:8080", "m")
    for bad in ("", "a b", 'a"b', "a'b", "a\\b", "a\nb"):
        with pytest.raises(ValueError):
            client_snippets("http://127.0.0.1:8080", bad)


def test_e3_keys():
    assert set(client_snippets("http://127.0.0.1:8080", "m")) == {"env", "curl", "python"}


def test_e4_env():
    assert client_snippets("http://127.0.0.1:8080/", "qwen3-30b")["env"] == (
        "export OPENAI_BASE_URL=http://127.0.0.1:8080/v1\nexport OPENAI_MODEL=qwen3-30b\n")


def test_e5_curl():
    assert client_snippets("http://127.0.0.1:8080/", "qwen3-30b")["curl"] == (
        "curl http://127.0.0.1:8080/v1/chat/completions \\\n"
        '  -H "Content-Type: application/json" \\\n'
        '  -H "Authorization: Bearer $OPENAI_API_KEY" \\\n'
        f"  -d '{BODY}'\n")


def test_e6_python():
    assert client_snippets("http://127.0.0.1:8080/", "qwen3-30b")["python"] == (
        "import os\nfrom openai import OpenAI\n\n"
        'client = OpenAI(base_url="http://127.0.0.1:8080/v1", '
        'api_key=os.environ.get("OPENAI_API_KEY", "none"))\n'
        'reply = client.chat.completions.create(model="qwen3-30b", '
        'messages=[{"role": "user", "content": "Say hello"}], max_tokens=16)\n'
        "print(reply.choices[0].message.content)\n")


def test_e7_custom_env_name_and_no_secret():
    s = client_snippets("https://box.lan", "m", api_key_env="LLAMA_KEY")
    assert "Bearer $LLAMA_KEY" in s["curl"]
    assert 'os.environ.get("LLAMA_KEY", "none")' in s["python"]
    assert "OPENAI_API_KEY" not in s["curl"] + s["python"]
