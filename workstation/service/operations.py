"""Operation IDs, states, progress events and cancellation (M1). Planned: #36."""

from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock

from workstation.errors import InvalidTransition


OP_STATES = ("queued", "running", "cancelling", "succeeded", "failed", "cancelled")


class OperationRegistry:
    """In-memory list of long jobs; ``clock()`` returns a UTC ISO string."""

    def __init__(self, *, clock=None):
        self.clock = clock or self._utc_now
        self._operations = {}
        self._events = []
        self._next_id = 1
        self._lock = RLock()

    @staticmethod
    def _utc_now():
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _operation(self, op_id):
        try:
            return self._operations[op_id]
        except KeyError:
            raise KeyError(op_id) from None

    def _record_change(self, operation, at):
        operation["updated_at"] = at
        self._events.append({
            "seq": len(self._events) + 1,
            "op_id": operation["id"],
            "state": operation["state"],
            "progress": operation["progress"],
            "message": operation["message"],
            "at": at,
        })

    def create(self, kind, *, message="", detail=None) -> str:
        with self._lock:
            op_id = f"op-{self._next_id:06d}"
            self._next_id += 1
            at = self.clock()
            operation = {
                "id": op_id,
                "kind": kind,
                "state": "queued",
                "progress": 0.0,
                "message": message,
                "detail": deepcopy(detail),
                "created_at": at,
                "updated_at": at,
            }
            self._operations[op_id] = operation
            self._record_change(operation, at)
            return op_id

    def get(self, op_id) -> dict:
        with self._lock:
            return deepcopy(self._operation(op_id))

    def start(self, op_id, *, message=None):
        with self._lock:
            operation = self._operation(op_id)
            if operation["state"] != "queued":
                raise InvalidTransition(f"cannot start operation in {operation['state']} state")
            at = self.clock()
            operation["state"] = "running"
            if message is not None:
                operation["message"] = message
            self._record_change(operation, at)

    def progress(self, op_id, fraction, *, message=None):
        if not 0 <= fraction <= 1:
            raise ValueError("fraction must be between 0 and 1")
        with self._lock:
            operation = self._operation(op_id)
            if operation["state"] not in ("running", "cancelling"):
                raise InvalidTransition(f"cannot update progress in {operation['state']} state")
            at = self.clock()
            operation["progress"] = fraction
            if message is not None:
                operation["message"] = message
            self._record_change(operation, at)

    def finish(self, op_id, *, ok, message=None, detail=None):
        with self._lock:
            operation = self._operation(op_id)
            if operation["state"] not in ("running", "cancelling"):
                raise InvalidTransition(f"cannot finish operation in {operation['state']} state")
            at = self.clock()
            operation["state"] = "succeeded" if ok else "failed"
            if ok:
                operation["progress"] = 1.0
            if message is not None:
                operation["message"] = message
            if detail is not None:
                operation["detail"] = deepcopy(detail)
            self._record_change(operation, at)

    def cancel(self, op_id):
        with self._lock:
            operation = self._operation(op_id)
            state = operation["state"]
            if state not in ("queued", "running"):
                return
            at = self.clock()
            operation["state"] = "cancelled" if state == "queued" else "cancelling"
            self._record_change(operation, at)

    def acknowledge_cancel(self, op_id, *, message=None):
        with self._lock:
            operation = self._operation(op_id)
            if operation["state"] != "cancelling":
                raise InvalidTransition(
                    f"cannot acknowledge cancellation in {operation['state']} state"
                )
            at = self.clock()
            operation["state"] = "cancelled"
            if message is not None:
                operation["message"] = message
            self._record_change(operation, at)

    def cancel_requested(self, op_id) -> bool:
        with self._lock:
            return self._operation(op_id)["state"] == "cancelling"

    def events_since(self, seq=0) -> list:
        with self._lock:
            return deepcopy([event for event in self._events if event["seq"] > seq])
