"""Host snapshot: hardware, OS/kernel, devices, memory, disk (shared contract). Planned: #32.

Linux only at run time; ``root`` lets tests point it at a fake file tree on any OS.
"""


def take_snapshot(*, root="/", model_dir=None, clock=None) -> dict:
    raise NotImplementedError("TODO #32")
