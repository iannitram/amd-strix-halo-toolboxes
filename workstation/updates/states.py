"""The update state machine (R2). Planned: #20."""

STATES = (
    "resolving", "pulling", "staging", "checking", "candidate-ready",
    "promoting", "active", "failed", "restoring",
)

# state -> frozenset of states it may move to; filled in by the issue.
TRANSITIONS = {}


def can_transition(current: str, target: str) -> bool:
    raise NotImplementedError("TODO #20")


def transition(current: str, target: str) -> str:
    """Return ``target`` when the move is allowed; else ValueError/InvalidTransition."""
    raise NotImplementedError("TODO #20")


def is_settled(state: str) -> bool:
    raise NotImplementedError("TODO #20")
