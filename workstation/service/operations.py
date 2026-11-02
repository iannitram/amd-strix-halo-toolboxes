"""Operation IDs, states, progress events and cancellation (M1). Planned: #36."""

OP_STATES = ("queued", "running", "cancelling", "succeeded", "failed", "cancelled")


class OperationRegistry:
    """In-memory list of long jobs; `clock()` returns a UTC ISO string."""

    def __init__(self, *, clock=None):
        self.clock = clock
        raise NotImplementedError("TODO #36")

    def create(self, kind, *, message="", detail=None) -> str:
        raise NotImplementedError("TODO #36")

    def get(self, op_id) -> dict:
        raise NotImplementedError("TODO #36")

    def start(self, op_id, *, message=None):
        raise NotImplementedError("TODO #36")

    def progress(self, op_id, fraction, *, message=None):
        raise NotImplementedError("TODO #36")

    def finish(self, op_id, *, ok, message=None, detail=None):
        raise NotImplementedError("TODO #36")

    def cancel(self, op_id):
        raise NotImplementedError("TODO #36")

    def acknowledge_cancel(self, op_id, *, message=None):
        raise NotImplementedError("TODO #36")

    def cancel_requested(self, op_id) -> bool:
        raise NotImplementedError("TODO #36")

    def events_since(self, seq=0) -> list:
        raise NotImplementedError("TODO #36")
