"""
Field data structure representing an agricultural field with obstacles.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from shapely.geometry import Point, Polygon


@dataclass
class FieldParameters:
    """Input parameters for coverage path planning."""

    operating_width: float  # Effective width of implement (meters)
    turning_radius: float  # Minimum turning radius of vehicle (meters)
    num_headland_passes: int  # Number of headland passes around field/obstacles
    driving_direction: float  # Angle in degrees (0 = horizontal)
    obstacle_threshold: float  # Threshold τ for Type A obstacle classification

    def __post_init__(self):
        """Validate parameters."""
        if self.operating_width <= 0:
            raise ValueError("Operating width must be positive")
        if self.turning_radius < 0:
            raise ValueError("Turning radius must be non-negative")
        if self.num_headland_passes < 0:
            raise ValueError("Number of headland passes must be non-negative")


@dataclass
class Field:
    """
    Represents an agricultural field with boundary and obstacles.

    Attributes:
        boundary: List of (x, y) coordinates defining field boundary (clockwise)
        obstacles: List of obstacle polygons, each as list of (x, y) coordinates
        name: Optional field identifier
    """

    boundary: List[Tuple[float, float]]
    obstacles: List[List[Tuple[float, float]]] = field(default_factory=list)
    name: Optional[str] = None

    # Processed geometries (computed lazily)
    _boundary_polygon: Optional[Polygon] = field(default=None, init=False, repr=False)
    _obstacle_polygons: Optional[List[Polygon]] = field(default=None, init=False, repr=False)
    _area: Optional[float] = field(default=None, init=False, repr=False)

    def __post_init__(self):
        """Validate field definition."""
        if len(self.boundary) < 3:
            raise ValueError("Field boundary must have at least 3 vertices")

        # Ensure boundary is clockwise
        self._ensure_clockwise_boundary()

    def _ensure_clockwise_boundary(self):
        """Ensure boundary vertices are in clockwise order."""
        poly = Polygon(self.boundary)
        if poly.exterior.is_ccw:
            self.boundary = list(reversed(self.boundary))

    @property
    def boundary_polygon(self) -> Polygon:
        """Get Shapely Polygon for field boundary."""
        if self._boundary_polygon is None:
            self._boundary_polygon = Polygon(self.boundary)
        return self._boundary_polygon

    @property
    def obstacle_polygons(self) -> List[Polygon]:
        """Get Shapely Polygons for obstacles."""
        if self._obstacle_polygons is None:
            self._obstacle_polygons = [Polygon(obs) for obs in self.obstacles]
        return self._obstacle_polygons

    @property
    def area(self) -> float:
        """Calculate field area (excluding obstacles)."""
        if self._area is None:
            total_area = self.boundary_polygon.area
            obstacle_area = sum(poly.area for poly in self.obstacle_polygons)
            self._area = total_area - obstacle_area
        return self._area

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        """Get bounding box (min_x, min_y, max_x, max_y)."""
        return self.boundary_polygon.bounds

    def contains_point(self, point: Tuple[float, float]) -> bool:
        """Check if point is inside field (not in obstacles)."""
        p = Point(point)
        if not self.boundary_polygon.contains(p):
            return False
        return not any(obs.contains(p) for obs in self.obstacle_polygons)

    def get_num_obstacles(self) -> int:
        """Get number of obstacles."""
        return len(self.obstacles)

    def __repr__(self) -> str:
        name_str = f"'{self.name}'" if self.name else "Unnamed"
        return f"Field({name_str}, area={self.area:.2f}m², " f"obstacles={len(self.obstacles)})"


def create_rectangular_field(
    width: float,
    height: float,
    obstacles: Optional[List[List[Tuple[float, float]]]] = None,
    name: Optional[str] = None,
) -> Field:
    """
    Create a simple rectangular field.

    Args:
        width: Field width in meters
        height: Field height in meters
        obstacles: Optional list of obstacle polygons
        name: Optional field name

    Returns:
        Field object
    """
    boundary = [(0, 0), (width, 0), (width, height), (0, height)]
    return Field(boundary=boundary, obstacles=obstacles or [], name=name)


def create_field_with_rectangular_obstacles(
    field_width: float,
    field_height: float,
    obstacle_specs: List[Tuple[float, float, float, float]],
    name: Optional[str] = None,
) -> Field:
    """
    Create field with rectangular obstacles.

    Args:
        field_width: Field width in meters
        field_height: Field height in meters
        obstacle_specs: List of (x, y, width, height) for each obstacle
        name: Optional field name

    Returns:
        Field object with rectangular obstacles
    """
    obstacles = []
    for x, y, w, h in obstacle_specs:
        obstacle = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        obstacles.append(obstacle)

    return create_rectangular_field(field_width, field_height, obstacles, name)
