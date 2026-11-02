"""Errors shared by every workstation module."""


class WorkstationError(Exception):
    """Base class for workstation errors."""


class RecipeError(WorkstationError):
    """A recipe failed validation; ``errors`` lists every problem found, in order."""

    def __init__(self, errors):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors))


class InvalidTransition(WorkstationError):
    """A state machine was asked for a move it does not allow."""


class Refused(WorkstationError):
    """The local service refused a request (host, origin or CSRF check)."""
