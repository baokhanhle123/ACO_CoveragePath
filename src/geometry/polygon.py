"""
Polygon geometric operations using Shapely and pyclipper.
"""
from typing import List, Tuple, Union, Optional
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, LineString, Point
from shapely import affinity
import pyclipper


def offset_polygon(
    polygon: Union[Polygon, List[Tuple[float, float]]],
    distance: float,
    inward: bool = True
) -> Optional[Polygon]:
    """
    Offset a polygon inward or outward by a given distance.

    Args:
        polygon: Shapely Polygon or list of (x, y) coordinates
        distance: Offset distance (positive value)
        inward: If True, offset inward; if False, offset outward

    Returns:
        Offset polygon, or None if offset results in empty geometry
    """
    if isinstance(polygon, list):
        polygon = Polygon(polygon)

    if not polygon.is_valid:
        polygon = polygon.buffer(0)  # Fix invalid geometries

    # Shapely's buffer with negative distance for inward offset
    offset_dist = -abs(distance) if inward else abs(distance)

    try:
        result = polygon.buffer(
            offset_dist,
            cap_style='flat',
            join_style='mitre',
            mitre_limit=10.0
        )

        if result.is_empty:
            return None

        # Handle MultiPolygon result (take largest)
        if isinstance(result, MultiPolygon):
            result = max(result.geoms, key=lambda p: p.area)

        return result if isinstance(result, Polygon) else None

    except Exception as e:
        print(f"Warning: Polygon offset failed: {e}")
        return None


def offset_polygon_pyclipper(
    polygon: Union[Polygon, List[Tuple[float, float]]],
    distance: float,
    inward: bool = True,
    scale_factor: float = 1000.0
) -> Optional[Polygon]:
    """
    Offset polygon using pyclipper (more robust for complex cases).

    Args:
        polygon: Shapely Polygon or list of coordinates
        distance: Offset distance
        inward: Offset direction
        scale_factor: Scaling factor for integer conversion

    Returns:
        Offset polygon or None
    """
    if isinstance(polygon, list):
        polygon = Polygon(polygon)

    # Convert to integer coordinates for pyclipper
    coords = np.array(polygon.exterior.coords[:-1])  # Remove duplicate last point
    scaled_coords = (coords * scale_factor).astype(np.int64).tolist()

    # Create clipper object
    pco = pyclipper.PyclipperOffset()

    # Determine offset direction
    offset_dist = abs(distance) * scale_factor
    if inward:
        offset_dist = -offset_dist

    try:
        pco.AddPath(scaled_coords, pyclipper.JT_MITER, pyclipper.ET_CLOSEDPOLYGON)
        solution = pco.Execute(offset_dist)

        if not solution:
            return None

        # Convert back to float coordinates
        offset_coords = np.array(solution[0]) / scale_factor
        return Polygon(offset_coords)

    except Exception as e:
        print(f"Warning: Pyclipper offset failed: {e}")
        return None


def polygon_intersection(poly1: Polygon, poly2: Polygon) -> Optional[Polygon]:
    """
    Compute intersection of two polygons.

    Returns:
        Intersection polygon, or None if no intersection
    """
    result = poly1.intersection(poly2)

    if result.is_empty:
        return None

    if isinstance(result, Polygon):
        return result
    elif isinstance(result, MultiPolygon):
        return max(result.geoms, key=lambda p: p.area)
    else:
        return None


def polygon_union(polygons: List[Polygon]) -> Union[Polygon, MultiPolygon]:
    """
    Compute union of multiple polygons.

    Returns:
        Union as Polygon or MultiPolygon
    """
    if not polygons:
        raise ValueError("Need at least one polygon")

    result = polygons[0]
    for poly in polygons[1:]:
        result = result.union(poly)

    return result


def minimum_distance_between_polygons(poly1: Polygon, poly2: Polygon) -> float:
    """
    Calculate minimum distance between two polygons.

    Returns:
        Minimum distance (0 if polygons intersect)
    """
    return poly1.distance(poly2)


def point_in_polygon(point: Tuple[float, float], polygon: Polygon) -> bool:
    """
    Check if a point is inside a polygon.

    Args:
        point: (x, y) coordinates
        polygon: Shapely Polygon

    Returns:
        True if point is inside polygon
    """
    return polygon.contains(Point(point))


def rotate_polygon(
    polygon: Union[Polygon, List[Tuple[float, float]]],
    angle_degrees: float,
    origin: Union[str, Tuple[float, float]] = 'center'
) -> Polygon:
    """
    Rotate a polygon around a point.

    Args:
        polygon: Shapely Polygon or list of coordinates
        angle_degrees: Rotation angle in degrees (counter-clockwise)
        origin: Rotation origin ('center', 'centroid', or (x, y) tuple)

    Returns:
        Rotated polygon
    """
    if isinstance(polygon, list):
        polygon = Polygon(polygon)

    return affinity.rotate(polygon, angle_degrees, origin=origin)


def translate_polygon(
    polygon: Union[Polygon, List[Tuple[float, float]]],
    xoff: float,
    yoff: float
) -> Polygon:
    """
    Translate (shift) a polygon.

    Args:
        polygon: Shapely Polygon or list of coordinates
        xoff: X offset
        yoff: Y offset

    Returns:
        Translated polygon
    """
    if isinstance(polygon, list):
        polygon = Polygon(polygon)

    return affinity.translate(polygon, xoff=xoff, yoff=yoff)


def simplify_polygon(polygon: Polygon, tolerance: float = 0.1) -> Polygon:
    """
    Simplify polygon geometry (reduce vertices).

    Args:
        polygon: Shapely Polygon
        tolerance: Simplification tolerance (larger = more simplification)

    Returns:
        Simplified polygon
    """
    return polygon.simplify(tolerance, preserve_topology=True)


def get_polygon_bounds(polygon: Polygon) -> Tuple[float, float, float, float]:
    """
    Get bounding box of polygon.

    Returns:
        (min_x, min_y, max_x, max_y)
    """
    return polygon.bounds


def ensure_clockwise(coords: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    Ensure polygon coordinates are in clockwise order.

    Args:
        coords: List of (x, y) coordinates

    Returns:
        Coordinates in clockwise order
    """
    poly = Polygon(coords)
    if poly.exterior.is_ccw:  # Counter-clockwise
        return list(reversed(coords))
    return coords


def ensure_counter_clockwise(coords: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    Ensure polygon coordinates are in counter-clockwise order.

    Args:
        coords: List of (x, y) coordinates

    Returns:
        Coordinates in counter-clockwise order
    """
    poly = Polygon(coords)
    if not poly.exterior.is_ccw:  # Clockwise
        return list(reversed(coords))
    return coords
