"""The skeleton imports everywhere and the upstream estimator CLI still works."""

import importlib
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]

MODULES = [
    "workstation", "workstation.errors", "workstation.redact", "workstation.__main__",
    "workstation.recipes.identity", "workstation.recipes.schema", "workstation.recipes.io",
    "workstation.recipes.migrate", "workstation.recipes.store", "workstation.recipes.digests",
    "workstation.updates.states", "workstation.updates.retention",
    "workstation.updates.transaction", "workstation.updates.drain",
    "workstation.qualification.gates", "workstation.qualification.compare",
    "workstation.qualification.runner", "workstation.qualification.manifest",
    "workstation.planning.memory", "workstation.planning.disk", "workstation.planning.labels",
    "workstation.planning.gguf_meta", "workstation.planning.remote_meta",
    "workstation.planning.planner", "workstation.host.snapshot",
    "workstation.runtime.port", "workstation.runtime.fake", "workstation.runtime.podman",
    "workstation.service.security", "workstation.service.operations", "workstation.service.app",
    "workstation.connections.snippets", "workstation.connections.check",
    "workstation.connections.endpoint",
]


@pytest.mark.parametrize("name", MODULES)
def test_module_imports(name):
    importlib.import_module(name)


def test_web_files_exist():
    for name in ("index.html", "styles.css", "app.js"):
        assert (ROOT / "workstation" / "web" / name).is_file()


def test_cli_help():
    from workstation.__main__ import main
    assert main(["--help"]) == 0


def test_upstream_estimator_cli_unchanged():
    script = ROOT / "toolboxes" / "gguf-vram-estimator.py"
    out = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True)
    assert out.returncode == 0
    assert "gguf_file" in out.stdout
