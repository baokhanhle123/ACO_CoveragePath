"""
Field-work track generation for complete coverage.

Implements parallel track generation from Zhou et al. 2014 (Section 2.2.3).
"""
from typing import List, Tuple
import numpy as np
from shapely.geometry import Polygon, LineString, Point
from shapely import affinity

from ..data.track import Track
from .mbr import get_mbr_with_orientation


def generate_parallel_tracks(
    inner_boundary: Polygon,
    driving_direction_degrees: float,
    operating_width: float
) -> List[Track]:
    """
    Generate parallel field-work tracks to cover the field body.

    Algorithm from paper (Section 2.2.3):
    1. Generate MBR of inner field boundary with edge parallel to driving direction
    2. Create reference line l parallel to θ
    3. Find vertex v with longest perpendicular distance from l
    4. Calculate number of tracks: n = ⌈|vv'|/w⌉
    5. Generate parallel lines with spacing w
    6. Subdivide lines at boundary intersections
    7. Keep segments inside field, discard outside

    Args:
        inner_boundary: Inner boundary polygon of field body
        driving_direction_degrees: Driving direction angle (degrees)
        operating_width: Effective operating width (w)

    Returns:
        List of Track objects covering the field
    """
    # Step 1: Get MBR aligned with driving direction
    mbr = get_mbr_with_orientation(inner_boundary, driving_direction_degrees)

    # Step 2: Create reference line parallel to driving direction
    # Place reference line at one vertex of MBR
    reference_point = mbr[0]  # Start at first vertex

    # Direction vector
    angle_rad = np.radians(driving_direction_degrees)
    direction_vector = np.array([np.cos(angle_rad), np.sin(angle_rad)])
    perpendicular_vector = np.array([-np.sin(angle_rad), np.cos(angle_rad)])

    # Step 3: Find vertex with longest perpendicular distance from reference line
    max_distance = 0
    for vertex in mbr:
        # Vector from reference point to vertex
        vec = vertex - reference_point

        # Perpendicular distance (dot product with perpendicular vector)
        distance = abs(np.dot(vec, perpendicular_vector))

        if distance > max_distance:
            max_distance = distance

    # Step 4: Calculate number of tracks
    num_tracks = int(np.ceil(max_distance / operating_width))

    if num_tracks == 0:
        return []

    # Step 5: Generate parallel line segments
    # Find field bounds to create long enough lines
    field_bounds = inner_boundary.bounds  # (minx, miny, maxx, maxy)
    field_diagonal = np.sqrt(
        (field_bounds[2] - field_bounds[0])**2 +
        (field_bounds[3] - field_bounds[1])**2
    )

    # Make lines longer than field diagonal to ensure coverage
    line_length = field_diagonal * 2

    tracks = []
    track_index = 0

    # Generate tracks from reference line
    for i in range(num_tracks):
        # Distance from reference line (first track at w/2, then increments of w)
        offset_distance = (i + 0.5) * operating_width

        # Offset point perpendicular to driving direction
        offset_point = reference_point + perpendicular_vector * offset_distance

        # Create line segment parallel to driving direction
        line_start = offset_point - direction_vector * (line_length / 2)
        line_end = offset_point + direction_vector * (line_length / 2)

        line = LineString([line_start, line_end])

        # Step 6: Find intersections with inner boundary
        intersection = line.intersection(inner_boundary)

        # Step 7: Extract line segments inside field
        segments = _extract_line_segments(intersection)

        # Create Track objects for each segment
        for seg_start, seg_end in segments:
            track = Track(
                start=seg_start,
                end=seg_end,
                index=track_index,
                block_id=None  # Will be assigned during clustering
            )
            tracks.append(track)
            track_index += 1

    return tracks


def _extract_line_segments(geometry) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
    """
    Extract line segments from intersection geometry.

    Args:
        geometry: Result of line.intersection(polygon)

    Returns:
        List of (start, end) tuples for each line segment
    """
    from shapely.geometry import GeometryCollection, MultiLineString

    segments = []

    if geometry.is_empty:
        return segments

    if isinstance(geometry, LineString):
        coords = list(geometry.coords)
        if len(coords) >= 2:
            segments.append(((coords[0][0], coords[0][1]), (coords[-1][0], coords[-1][1])))

    elif isinstance(geometry, MultiLineString):
        for line in geometry.geoms:
            coords = list(line.coords)
            if len(coords) >= 2:
                segments.append(((coords[0][0], coords[0][1]), (coords[-1][0], coords[-1][1])))

    elif isinstance(geometry, GeometryCollection):
        for geom in geometry.geoms:
            if isinstance(geom, LineString):
                coords = list(geom.coords)
                if len(coords) >= 2:
                    segments.append(((coords[0][0], coords[0][1]), (coords[-1][0], coords[-1][1])))

    elif isinstance(geometry, Point):
        # Single point intersection - skip
        pass

    return segments


def order_tracks_by_position(tracks: List[Track], driving_direction_degrees: float) -> List[Track]:
    """
    Order tracks by their position perpendicular to driving direction.

    Args:
        tracks: List of Track objects
        driving_direction_degrees: Driving direction

    Returns:
        Ordered list of tracks
    """
    if not tracks:
        return []

    angle_rad = np.radians(driving_direction_degrees)
    perpendicular_vector = np.array([-np.sin(angle_rad), np.cos(angle_rad)])

    # Calculate position of each track (use midpoint)
    track_positions = []
    for track in tracks:
        midpoint = np.array(track.midpoint)
        position = np.dot(midpoint, perpendicular_vector)
        track_positions.append((position, track))

    # Sort by position
    track_positions.sort(key=lambda x: x[0])

    # Re-index tracks
    ordered_tracks = []
    for new_index, (_, track) in enumerate(track_positions):
        track.index = new_index
        ordered_tracks.append(track)

    return ordered_tracks


def calculate_track_coverage_area(tracks: List[Track], operating_width: float) -> float:
    """
    Estimate total area covered by tracks.

    Args:
        tracks: List of Track objects
        operating_width: Operating width

    Returns:
        Approximate coverage area in square meters
    """
    total_length = sum(track.length for track in tracks)
    return total_length * operating_width


def get_track_endpoints(tracks: List[Track]) -> List[Tuple[float, float]]:
    """
    Extract all track endpoints for visualization.

    Args:
        tracks: List of Track objects

    Returns:
        List of all endpoint coordinates
    """
    endpoints = []
    for track in tracks:
        endpoints.append(track.start)
        endpoints.append(track.end)
    return endpoints
