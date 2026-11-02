from pathlib import Path

from workstation.host.snapshot import take_snapshot


def _tree(root: Path):
    (root / "proc/sys/kernel").mkdir(parents=True)
    (root / "proc/sys/kernel/osrelease").write_text("6.18.4-test\n", encoding="utf-8")
    (root / "proc").mkdir(exist_ok=True)
    (root / "proc/meminfo").write_text(
        "MemTotal:       1024 kB\nMemAvailable:    256 kB\n", encoding="utf-8"
    )
    (root / "sys/class/dmi/id").mkdir(parents=True)
    (root / "sys/class/dmi/id/bios_version").write_text("FW-1\n", encoding="utf-8")
    (root / "dev/dri").mkdir(parents=True)
    (root / "dev/dri/card0").touch()
    (root / "dev/kfd").touch()


def test_reads_fake_root_and_injected_versions(tmp_path):
    _tree(tmp_path)
    calls = []

    def runner(tool, timeout):
        calls.append((tool, timeout))
        return f"{tool} 1.2"

    result = take_snapshot(
        root=tmp_path, clock=lambda: "2026-01-02T03:04:05Z", version_runner=runner
    )

    assert result["kernel"] == "6.18.4-test"
    assert result["firmware"] == "FW-1"
    assert result["gpu_device_nodes"] == ["/dev/dri/card0", "/dev/kfd"]
    assert result["memory"] == {"total_bytes": 1024 * 1024, "free_bytes": 256 * 1024}
    assert result["disk_free_bytes"] is not None
    assert result["versions"] == {"toolbox": "toolbox 1.2", "podman": "podman 1.2"}
    assert calls == [("toolbox", 2.0), ("podman", 2.0)]
    assert result["sampled_at"] == "2026-01-02T03:04:05Z"
    assert result["collection_failures"] == []


def test_missing_files_and_version_failures_are_partial(tmp_path):
    result = take_snapshot(
        root=tmp_path,
        model_dir="/missing-models",
        version_runner=lambda tool, timeout: (_ for _ in ()).throw(RuntimeError("unavailable")),
    )

    assert result["kernel"] is None
    assert result["firmware"] is None
    assert result["memory"] == {"total_bytes": None, "free_bytes": None}
    assert result["disk_free_bytes"] is None
    assert result["versions"] == {"toolbox": None, "podman": None}
    assert {failure["field"] for failure in result["collection_failures"]} >= {
        "kernel", "firmware", "memory", "memory.total_bytes", "disk_free_bytes",
        "versions.toolbox", "versions.podman",
    }


def test_default_version_calls_are_linux_only_on_live_root(monkeypatch):
    import workstation.host.snapshot as module

    monkeypatch.setattr(module.platform, "system", lambda: "Windows")
    result = take_snapshot(root="/")
    assert result["versions"] == {"toolbox": None, "podman": None}
    fields = {failure["field"] for failure in result["collection_failures"]}
    assert {"versions.toolbox", "versions.podman"} <= fields
