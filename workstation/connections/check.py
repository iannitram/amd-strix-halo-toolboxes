"""Check an OpenAI-compatible endpoint: list models and request a short completion (M3)."""

import json as json_module
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _request(method: str, url: str, *, json: dict | None, timeout: float):
    data = None if json is None else json_module.dumps(json).encode("utf-8")
    headers = {} if data is None else {"Content-Type": "application/json"}
    request = Request(url, data=data, headers=headers, method=method)
    with urlopen(request, timeout=timeout) as response:
        return response.status, response.read()


def _status(response) -> int:
    if isinstance(response, tuple):
        return int(response[0])
    return int(response.status)


def _step(method, url, *, payload, timeout_s, http):
    try:
        response = http(method, url, json=payload, timeout=timeout_s)
        status = _status(response)
        result = {"passed": 200 <= status < 300, "status": status}
        if not result["passed"]:
            result["error"] = f"HTTP {status}"
        return result
    except HTTPError as error:
        return {
            "passed": False,
            "status": error.code,
            "error": f"HTTP {error.code}: {error.reason}",
        }
    except (URLError, TimeoutError, OSError, ValueError) as error:
        return {"passed": False, "error": str(error) or type(error).__name__}
    except Exception as error:
        return {"passed": False, "error": str(error) or type(error).__name__}


def check_endpoint(base_url: str, model: str, *, timeout_s: float = 30.0, http=None) -> dict:
    """Check model listing and a 16-token chat completion, reporting each step."""
    base = base_url.rstrip("/")
    send = http or _request
    models = _step("GET", f"{base}/v1/models", payload=None, timeout_s=timeout_s, http=send)
    completion = _step(
        "POST",
        f"{base}/v1/chat/completions",
        payload={
            "model": model,
            "messages": [{"role": "user", "content": "Reply with OK."}],
            "max_tokens": 16,
        },
        timeout_s=timeout_s,
        http=send,
    )
    steps = {"list_models": models, "completion": completion}
    return {"passed": all(step["passed"] for step in steps.values()), "steps": steps}
