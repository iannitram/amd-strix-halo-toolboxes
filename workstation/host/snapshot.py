"""Read a best-effort, root-scoped host snapshot (R3, #32)."""

import platform
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path


def _default_version_runner(tool: str, timeout: float) -> str:
    result = subprocess.run(
        [tool, "--version"], capture_output=True, text=True, timeout=timeout, check=False
    )
    if result.returncode:
        raise RuntimeError(f"{tool} --version exited with status {result.returncode}")
    return (result.stdout or result.stderr).strip()


def _read(path: Path, failures: list, label: str) -> str | None:
    try:
        return path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        failures.append({"field": label, "reason": str(exc)})
        return None


def _rooted(root: Path, path) -> Path:
    # Handle "/x" as rooted on every OS: pathlib on Windows does not treat "/x" as absolute.
    text = str(path).replace("\\", "/")
    if text.startswith("/"):
        return root.joinpath(*[part for part in text.split("/") if part])
    return root / text


def _version(tool: str, runner, failures: list):
    try:
        value = runner(tool, 2.0)
        return str(value).strip() or None
    except Exception as exc:  # A version command must never invalidate the snapshot.
        failures.append({"field": f"versions.{tool}", "reason": str(exc)})
        return None


def take_snapshot(*, root="/", model_dir=None, clock=None, version_runner=None) -> dict:
    """Collect host facts without changing the host.

    ``root`` remaps absolute proc, sys, dev and disk paths, allowing fixture trees on
    any platform. ``version_runner`` receives ``(tool, timeout_seconds)``.
    """
    root_path = Path(root)
    failures = []
    now = clock() if clock else datetime.now(timezone.utc).isoformat()
    if isinstance(now, datetime):
        now = now.isoformat()
    runner = version_runner or _default_version_runner

    kernel = _read(_rooted(root_path, "/proc/sys/kernel/osrelease"), failures, "kernel")
    firmware_path = _rooted(root_path, "/sys/class/dmi/id/bios_version")
    firmware = _read(firmware_path, failures, "firmware")

    meminfo = _read(_rooted(root_path, "/proc/meminfo"), failures, "memory")
    memory = {"total_bytes": None, "free_bytes": None}
    if meminfo is None:
        for key in memory:
            failures.append({"field": f"memory.{key}", "reason": "memory data unavailable"})
    else:
        parsed = {}
        for line in meminfo.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0].rstrip(":") in {"MemTotal", "MemAvailable"}:
                try:
                    parsed[parts[0].rstrip(":")] = int(parts[1]) * 1024
                except ValueError:
                    pass
        for key, source in (("total_bytes", "MemTotal"), ("free_bytes", "MemAvailable")):
            memory[key] = parsed.get(source)
            if memory[key] is None:
                failures.append({"field": f"memory.{key}", "reason": f"{source} unavailable"})

    device_dir = _rooted(root_path, "/dev")
    devices = None
    try:
        if not device_dir.is_dir():
            raise OSError(f"{device_dir} is not a readable directory")
        nodes = []
        dri = device_dir / "dri"
        if dri.is_dir():
            nodes.extend(f"/dev/dri/{entry.name}" for entry in sorted(dri.iterdir()))
        if (device_dir / "kfd").exists():
            nodes.append("/dev/kfd")
        devices = nodes
    except OSError as exc:
        failures.append({"field": "devices", "reason": str(exc)})

    disk_path = _rooted(root_path, model_dir if model_dir is not None else "/")
    try:
        disk_free = shutil.disk_usage(disk_path).free
    except OSError as exc:
        disk_free = None
        failures.append({"field": "disk_free_bytes", "reason": str(exc)})

    versions = {"toolbox": None, "podman": None}
    if platform.system() == "Linux" or version_runner is not None:
        versions = {tool: _version(tool, runner, failures) for tool in versions}
    else:
        for tool in versions:
            failures.append({"field": f"versions.{tool}", "reason": "available on Linux only"})

    return {
        "schema_version": 1,
        "id": str(uuid.uuid4()),
        "sampled_at": now,
        "kernel": kernel,
        "firmware": firmware,
        "gpu_device_nodes": devices,
        "memory": memory,
        "disk_free_bytes": disk_free,
        "versions": versions,
        "collection_failures": failures,
    }
