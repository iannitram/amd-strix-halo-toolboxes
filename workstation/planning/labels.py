"""Label each number as estimated, measured, stale or unknown (P1). Planned: #29."""

import re
from datetime import datetime, timezone

LABELS = ("estimated", "measured", "stale", "unknown")


def label_value(value, *, source, observed_at=None, now=None, stale_after_s=300) -> dict:
    if source not in ("estimate", "measured"):
        raise ValueError(f"unknown source: {source}")

    if value is None:
        return {"value": None, "label": "unknown", "source": source, "age_s": None}

    if source == "estimate":
        return {"value": value, "label": "estimated", "source": source, "age_s": None}

    if observed_at is None or now is None:
        return {"value": value, "label": "stale", "source": source, "age_s": None}

    def parse_time(timestamp):
        if timestamp.endswith("Z"):
            timestamp = f"{timestamp[:-1]}+00:00"
        # Python 3.10 parses fractional seconds only with exactly 3 or 6 digits; pad to 6.
        timestamp = re.sub(r"\.(\d+)", lambda m: "." + m.group(1).ljust(6, "0")[:6],
                           timestamp, count=1)
        parsed = datetime.fromisoformat(timestamp)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed

    age_s = int((parse_time(now) - parse_time(observed_at)).total_seconds())
    label = "measured" if age_s <= stale_after_s else "stale"
    return {"value": value, "label": label, "source": source, "age_s": age_s}
