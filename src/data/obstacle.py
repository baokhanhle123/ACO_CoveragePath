"""
Obstacle data structure and classification types.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

from shapely.geometry import Polygon


class ObstacleType(Enum):
    """
    Obstacle classification according to Zhou et al. 2014:

    Type A: Small obstacle that doesn't affect coverage plan
            (dimension perpendicular to driving direction < threshold τ)

    Type B: Obstacle intersecting with field inner boundary
            (incorporated into field headland)

    Type C: Obstacles in close proximity (min distance < operating width)
            (merged into minimal bounding polygon)

    Type D: Standard obstacle requiring field decomposition
            (all remaining obstacles + merged Type C)
    """

    A = "Type A - Ignorable"
    B = "Type B - Boundary-touching"
    C = "Type C - Close proximity"
    D = "Type D - Requires decomposition"


@dataclass
class Obstacle:
    """
    Represents an obstacle within the field.

    Attributes:
        boundary: List of (x, y) coordinates defining obstacle boundary
        obstacle_type: Classification type (A, B, C, or D)
        index: Original obstacle index
        merged_from: List of original obstacle indices if merged (Type C)
    """

    boundary: List[Tuple[float, float]]
    obstacle_type: ObstacleType
    index: int
    merged_from: Optional[List[int]] = None

    _polygon: Optional[Polygon] = None

    @property
    def polygon(self) -> Polygon:
        """Get Shapely Polygon representation."""
        if self._polygon is None:
            self._polygon = Polygon(self.boundary)
        return self._polygon

    @property
    def area(self) -> float:
        """Calculate obstacle area."""
        return self.polygon.area

    @property
    def centroid(self) -> Tuple[float, float]:
        """Get obstacle centroid."""
        c = self.polygon.centroid
        return (c.x, c.y)

    def is_merged(self) -> bool:
        """Check if this obstacle is result of merging."""
        return self.merged_from is not None and len(self.merged_from) > 1

    def __repr__(self) -> str:
        merged_str = f", merged from {self.merged_from}" if self.is_merged() else ""
        return (
            f"Obstacle({self.index}, {self.obstacle_type.name}, "
            f"area={self.area:.2f}m²{merged_str})"
        )
