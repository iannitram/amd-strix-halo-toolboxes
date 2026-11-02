"""The resource plan: memory + disk + labels + backend-compatible alternatives (P1). Planned: #4."""


def plan(model_meta, choices, host) -> dict:
    raise NotImplementedError("TODO #4")


def alternatives(model_meta, choices, host, *, backend) -> list:
    raise NotImplementedError("TODO #4")
