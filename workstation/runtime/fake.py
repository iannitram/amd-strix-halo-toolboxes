"""In-memory RuntimePort with failure injection, for every default test. Planned: #22."""


class FakeRuntime:
    def __init__(self, *, fail_on=None):
        self.fail_on = dict(fail_on or {})
        raise NotImplementedError("TODO #22")
