"""Tests for the in-memory runtime used by default tests."""

import pytest

from workstation.runtime.fake import FakeRuntime


def test_fake_runtime_tracks_images_containers_and_servers():
    runtime = FakeRuntime()
    runtime.pull("example/model", "sha256:abc")
    runtime.create("model-box", "example/model@sha256:abc")
    handle = runtime.start_server({"model": "example/model"})

    assert runtime.images == {"example/model@sha256:abc"}
    assert runtime.containers == {"model-box": "example/model@sha256:abc"}
    assert runtime.servers[handle["id"]]["recipe"] == {"model": "example/model"}

    runtime.stop_server(handle)
    runtime.remove("model-box")
    assert runtime.servers == {}
    assert runtime.containers == {}


def test_fake_runtime_returns_scripted_values_as_copies():
    models = [{"id": "model-a"}]
    completion = {"text": "answer"}
    runtime = FakeRuntime(
        devices={"gpu": "test"},
        health="ready",
        active_requests=3,
        models=models,
        completion=completion,
    )
    handle = runtime.start_server({})

    assert runtime.devices() == {"gpu": "test"}
    assert runtime.health(handle) == "ready"
    assert runtime.active_requests(handle) == 3
    returned_models = runtime.list_models(handle)
    returned_completion = runtime.complete(handle, "prompt", max_tokens=2)
    returned_models.clear()
    returned_completion["text"] = "changed"
    assert runtime.list_models(handle) == models
    assert runtime.complete(handle, "prompt") == completion


@pytest.mark.parametrize(
    ("step", "invoke"),
    [
        ("devices", lambda runtime: runtime.devices()),
        ("pull", lambda runtime: runtime.pull("repo", "digest")),
        ("create", lambda runtime: runtime.create("box", "image")),
        ("remove", lambda runtime: runtime.remove("box")),
        ("start_server", lambda runtime: runtime.start_server({})),
        ("stop_server", lambda runtime: runtime.stop_server({"id": 1})),
        ("health", lambda runtime: runtime.health({})),
        ("active_requests", lambda runtime: runtime.active_requests({})),
        ("list_models", lambda runtime: runtime.list_models({})),
        ("complete", lambda runtime: runtime.complete({}, "prompt")),
    ],
)
def test_failure_can_be_injected_at_each_port_step(step, invoke):
    runtime = FakeRuntime(fail_on={step})
    with pytest.raises(RuntimeError, match=f"failure at {step}"):
        invoke(runtime)


def test_failure_mapping_can_supply_exception_instance():
    error = ValueError("injected")
    runtime = FakeRuntime(fail_on={"pull": error})

    with pytest.raises(ValueError, match="injected"):
        runtime.pull("repo", "digest")
