"""Check an OpenAI-compatible endpoint: list models, short completion, stream (M3). Planned: #44."""


def check_endpoint(base_url: str, model: str, *, timeout_s: float = 30.0, http=None) -> dict:
    raise NotImplementedError("TODO #44")
