"""The update state machine (R2)."""

from workstation.errors import InvalidTransition

STATES = (
    "resolving", "pulling", "staging", "checking", "candidate-ready",
    "promoting", "active", "failed", "restoring",
)

# state -> frozenset of states it may move to.
TRANSITIONS = {
    "resolving": frozenset({"pulling", "failed"}),
    "pulling": frozenset({"staging", "failed"}),
    "staging": frozenset({"checking", "failed"}),
    "checking": frozenset({"candidate-ready", "failed"}),
    "candidate-ready": frozenset({"promoting", "failed"}),
    "promoting": frozenset({"active", "failed", "restoring"}),
    "active": frozenset({"restoring"}),
    "failed": frozenset({"restoring"}),
    "restoring": frozenset({"active", "failed"}),
}


def can_transition(current: str, target: str) -> bool:
    return current in TRANSITIONS and target in TRANSITIONS[current]


def transition(current: str, target: str) -> str:
    """Return ``target`` when the move is allowed; else ValueError/InvalidTransition."""
    if current not in TRANSITIONS:
        raise ValueError(f"unknown state: {current}")
    if target not in TRANSITIONS:
        raise ValueError(f"unknown state: {target}")
    if not can_transition(current, target):
        raise InvalidTransition(f"{current} -> {target} is not allowed")
    return target


def is_settled(state: str) -> bool:
    if state not in TRANSITIONS:
        raise ValueError(f"unknown state: {state}")
    return state in {"active", "failed"}
