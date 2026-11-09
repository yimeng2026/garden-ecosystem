"""Shared errors with no embedded credentials."""


class GardenError(Exception):
    """An expected adapter error that is safe to present to the caller."""


class BudgetExceeded(GardenError):
    """The requested input and minimum output cannot fit the context window."""


class ApprovalRequired(GardenError):
    """An action cannot execute without explicit permission."""


class CheckpointMismatch(GardenError):
    """A checkpoint does not belong to the requested execution chain."""


class LearningDisabled(GardenError):
    """Learning was attempted while the default-disabled ledger is off."""
