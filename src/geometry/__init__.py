"""
Geometric processing modules for coverage path planning.
"""

from .headland import (
    HeadlandResult,
    calculate_headland_area,
    generate_field_headland,
    generate_obstacle_headland,
    get_headland_path_coordinates,
)
from .mbr import (
    compute_minimum_bounding_rectangle,
    get_mbr_dimensions,
    get_mbr_long_edge_direction,
    get_mbr_with_orientation,
)
from .polygon import (
    ensure_clockwise,
    ensure_counter_clockwise,
    minimum_distance_between_polygons,
    offset_polygon,
    point_in_polygon,
    polygon_intersection,
    polygon_union,
    rotate_polygon,
    translate_polygon,
)
from .tracks import (
    calculate_track_coverage_area,
    generate_parallel_tracks,
    get_track_endpoints,
    order_tracks_by_position,
)

__all__ = [
    # Polygon operations
    "offset_polygon",
    "polygon_intersection",
    "polygon_union",
    "minimum_distance_between_polygons",
    "point_in_polygon",
    "rotate_polygon",
    "translate_polygon",
    "ensure_clockwise",
    "ensure_counter_clockwise",
    # Headland
    "generate_field_headland",
    "generate_obstacle_headland",
    "HeadlandResult",
    "get_headland_path_coordinates",
    "calculate_headland_area",
    # MBR
    "compute_minimum_bounding_rectangle",
    "get_mbr_with_orientation",
    "get_mbr_dimensions",
    "get_mbr_long_edge_direction",
    # Tracks
    "generate_parallel_tracks",
    "order_tracks_by_position",
    "calculate_track_coverage_area",
    "get_track_endpoints",
]
