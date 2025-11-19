"""
Geometric processing modules for coverage path planning.
"""

from .polygon import (
    offset_polygon,
    polygon_intersection,
    polygon_union,
    minimum_distance_between_polygons,
    point_in_polygon,
    rotate_polygon,
    translate_polygon,
    ensure_clockwise,
    ensure_counter_clockwise,
)
from .headland import (
    generate_field_headland,
    generate_obstacle_headland,
    HeadlandResult,
    get_headland_path_coordinates,
    calculate_headland_area,
)
from .mbr import (
    compute_minimum_bounding_rectangle,
    get_mbr_with_orientation,
    get_mbr_dimensions,
    get_mbr_long_edge_direction,
)
from .tracks import (
    generate_parallel_tracks,
    order_tracks_by_position,
    calculate_track_coverage_area,
    get_track_endpoints,
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
