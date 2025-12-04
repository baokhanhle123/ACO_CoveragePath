"""
Field-work track generation for complete coverage.

Implements parallel track generation from Zhou et al. 2014 (Section 2.2.3).
"""

from typing import List, Optional, Tuple

import numpy as np
from shapely.geometry import LineString, MultiPolygon, Point, Polygon

from ..data.track import Track
from .mbr import get_mbr_with_orientation


def generate_parallel_tracks(
    inner_boundary: Polygon,
    driving_direction_degrees: float,
    operating_width: float,
    obstacles_to_avoid: Optional[List[Polygon]] = None,
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
    8. Filter out segments that intersect obstacles (e.g., Type B obstacles)

    Args:
        inner_boundary: Inner boundary polygon of field body
        driving_direction_degrees: Driving direction angle (degrees)
        operating_width: Effective operating width (w)
        obstacles_to_avoid: Optional list of obstacle polygons to exclude from tracks
                          (e.g., Type B obstacles that still physically exist)

    Returns:
        List of Track objects covering the field
    """
    # Step 0: Subtract obstacles from boundary if provided
    # Type B obstacles are incorporated into inner boundary but still physically exist
    # We need to ensure tracks don't cross them
    working_boundary = inner_boundary
    if obstacles_to_avoid:
        for obstacle in obstacles_to_avoid:
            try:
                # Subtract obstacle from boundary
                working_boundary = working_boundary.difference(obstacle)
                # Handle MultiPolygon result
                if isinstance(working_boundary, MultiPolygon):
                    # For track generation, we need to handle all parts
                    # Use union to combine all parts, or take largest if union fails
                    try:
                        # Try to get a single polygon by taking the largest piece
                        # This works well when obstacles create holes
                        working_boundary = max(working_boundary.geoms, key=lambda p: p.area)
                    except Exception:
                        # If that fails, try buffer(0) to clean up
                        working_boundary = working_boundary.buffer(0)
                        if isinstance(working_boundary, MultiPolygon):
                            working_boundary = max(working_boundary.geoms, key=lambda p: p.area)
            except Exception:
                # If difference fails, continue with original boundary
                pass
    
    # Step 1: Get MBR aligned with driving direction
    mbr = get_mbr_with_orientation(working_boundary, driving_direction_degrees)

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
    field_bounds = working_boundary.bounds  # (minx, miny, maxx, maxy)
    field_diagonal = np.sqrt(
        (field_bounds[2] - field_bounds[0]) ** 2 + (field_bounds[3] - field_bounds[1]) ** 2
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

        # Step 6: Find intersections with working boundary (obstacles already subtracted)
        intersection = line.intersection(working_boundary)

        # Step 7: Extract line segments inside field
        segments = _extract_line_segments(intersection)

        # Create Track objects for each segment
        for seg_start, seg_end in segments:
            track = Track(
                start=seg_start,
                end=seg_end,
                index=track_index,
                block_id=None,  # Will be assigned during clustering
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
