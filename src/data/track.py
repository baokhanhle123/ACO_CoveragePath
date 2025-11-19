"""
Track data structure representing a field-work track (parallel swath).
"""
from typing import Tuple, Optional
from dataclasses import dataclass
import numpy as np


@dataclass
class Track:
    """
    Represents a single field-work track (swath).

    Attributes:
        start: Starting point (x, y)
        end: Ending point (x, y)
        index: Track index in ordered sequence
        block_id: ID of block this track belongs to (None if unassigned)
    """

    start: Tuple[float, float]
    end: Tuple[float, float]
    index: int
    block_id: Optional[int] = None

    @property
    def length(self) -> float:
        """Calculate track length."""
        dx = self.end[0] - self.start[0]
        dy = self.end[1] - self.start[1]
        return np.sqrt(dx**2 + dy**2)

    @property
    def midpoint(self) -> Tuple[float, float]:
        """Calculate track midpoint."""
        return (
            (self.start[0] + self.end[0]) / 2,
            (self.start[1] + self.end[1]) / 2
        )

    @property
    def direction_vector(self) -> Tuple[float, float]:
        """Get normalized direction vector from start to end."""
        dx = self.end[0] - self.start[0]
        dy = self.end[1] - self.start[1]
        length = self.length
        if length == 0:
            return (0, 0)
        return (dx / length, dy / length)

    def reverse(self) -> 'Track':
        """Return a reversed copy of this track."""
        return Track(
            start=self.end,
            end=self.start,
            index=self.index,
            block_id=self.block_id
        )

    def __repr__(self) -> str:
        block_str = f", block={self.block_id}" if self.block_id is not None else ""
        return f"Track({self.index}, len={self.length:.2f}m{block_str})"
