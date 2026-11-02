"""In-memory RuntimePort with failure injection, for default tests."""

from copy import deepcopy
from itertools import count


class FakeRuntime:
    """A deterministic runtime double that never starts external processes."""

    def __init__(
        self,
        *,
        fail_on=None,
        devices=None,
        health="healthy",
        active_requests=0,
        models=None,
        completion=None,
    ):
        self.fail_on = self._normalize_failures(fail_on)
        self.images = set()
        self.containers = {}
        self.servers = {}
        self.devices_result = deepcopy(devices if devices is not None else {})
        self.health_result = health
        self.active_requests_result = active_requests
        self.models_result = deepcopy(models if models is not None else [])
        self.completion_result = deepcopy(
            completion if completion is not None else {"choices": [{"text": ""}]}
        )
        self._server_ids = count(1)

    @staticmethod
    def _normalize_failures(fail_on):
        if fail_on is None:
            return {}
        if isinstance(fail_on, dict):
            return dict(fail_on)
        return {step: None for step in fail_on}

    def _check_failure(self, step):
        if step not in self.fail_on:
            return
        failure = self.fail_on[step]
        if isinstance(failure, BaseException):
            raise failure
        raise RuntimeError(f"Fake runtime failure at {step}")

    def devices(self):
        self._check_failure("devices")
        return deepcopy(self.devices_result)

    def pull(self, repository: str, digest: str) -> None:
        self._check_failure("pull")
        self.images.add(f"{repository}@{digest}")

    def create(self, name: str, image_ref: str) -> None:
        self._check_failure("create")
        self.containers[name] = image_ref

    def remove(self, name: str) -> None:
        self._check_failure("remove")
        self.containers.pop(name, None)

    def start_server(self, recipe: dict) -> dict:
        self._check_failure("start_server")
        server_id = next(self._server_ids)
        handle = {"id": server_id}
        self.servers[server_id] = {"handle": deepcopy(handle), "recipe": deepcopy(recipe)}
        return deepcopy(handle)

    def stop_server(self, handle: dict) -> None:
        self._check_failure("stop_server")
        self.servers.pop(handle.get("id"), None)

    def health(self, handle: dict) -> str:
        self._check_failure("health")
        return deepcopy(self.health_result)

    def active_requests(self, handle: dict) -> int:
        self._check_failure("active_requests")
        return self.active_requests_result

    def list_models(self, handle: dict) -> list:
        self._check_failure("list_models")
        return deepcopy(self.models_result)

    def complete(self, handle: dict, prompt: str, *, max_tokens: int = 16) -> dict:
        self._check_failure("complete")
        return deepcopy(self.completion_result)
