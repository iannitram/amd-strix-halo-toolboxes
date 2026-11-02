"""Stage, check, promote and restore a candidate recipe (R2). Planned: #2.

Talks to the host only through a RuntimePort (workstation/runtime/port.py).
"""


class UpdateTransaction:
    def __init__(self, runtime, store, *, clock=None):
        self.runtime = runtime
        self.store = store
        self.clock = clock

    def stage(self, candidate):
        raise NotImplementedError("TODO #2")

    def promote(self):
        raise NotImplementedError("TODO #2")

    def restore(self):
        raise NotImplementedError("TODO #2")
