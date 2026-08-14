"""Action-agnostic semantic coverage evidence."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SemanticCoverage:
    """Describe support boundaries without knowing an Action's program or runtime model."""

    payload_executable: bool
    parent_executable: bool
    followup_executable: bool
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if any(not isinstance(reason, str) or not reason for reason in self.limitations):
            raise ValueError("semantic coverage limitations must be nonempty strings")
        if len(set(self.limitations)) != len(self.limitations):
            raise ValueError("semantic coverage limitations must be unique")

    @property
    def fully_supported(self) -> bool:
        return self.payload_executable and self.parent_executable and self.followup_executable
