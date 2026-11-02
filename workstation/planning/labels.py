"""Label each number as estimated, measured, stale or unknown (P1). Planned: #29."""

LABELS = ("estimated", "measured", "stale", "unknown")


def label_value(value, *, source, observed_at=None, now=None, stale_after_s=300) -> dict:
    raise NotImplementedError("TODO #29")
