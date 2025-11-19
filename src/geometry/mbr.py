"""
Minimum Bounding Rectangle (MBR) calculation using rotating calipers.

Implements minimum-perimeter bounding rectangle as used in Zhou et al. 2014
for track generation.
"""

from typing import Tuple

import numpy as np
from scipy.spatial import ConvexHull
from shapely.geometry import Polygon


def compute_minimum_bounding_rectangle(polygon: Polygon) -> Tuple[np.ndarray, float]:
    """
    Compute minimum-perimeter bounding rectangle using rotating calipers.

    Args:
        polygon: Input polygon

    Returns:
        Tuple of (rectangle_coords, angle):
            - rectangle_coords: (4, 2) array of rectangle corners
            - angle: Orientation angle in degrees of the rectangle
    """
    # Get convex hull of polygon
    coords = np.array(polygon.exterior.coords[:-1])  # Remove duplicate last point

    if len(coords) < 3:
        raise ValueError("Polygon must have at least 3 points")

    try:
        hull = ConvexHull(coords)
        hull_points = coords[hull.vertices]
    except Exception:
        # If convex hull fails, use original points
        hull_points = coords

    # Rotating calipers algorithm
    min_perimeter = float("inf")
    best_rectangle = None
    best_angle = 0.0

    num_points = len(hull_points)

    # Check each edge of the convex hull
    for i in range(num_points):
        # Get edge vector
        p1 = hull_points[i]
        p2 = hull_points[(i + 1) % num_points]
        edge_vector = p2 - p1
        edge_angle = np.arctan2(edge_vector[1], edge_vector[0])

        # Rotate points to align edge with x-axis
        rotation_angle = -edge_angle
        cos_angle = np.cos(rotation_angle)
        sin_angle = np.sin(rotation_angle)

        rotation_matrix = np.array([[cos_angle, -sin_angle], [sin_angle, cos_angle]])

        rotated_points = hull_points @ rotation_matrix.T

        # Find bounding box in rotated coordinates
        min_x = np.min(rotated_points[:, 0])
        max_x = np.max(rotated_points[:, 0])
        min_y = np.min(rotated_points[:, 1])
        max_y = np.max(rotated_points[:, 1])

        width = max_x - min_x
        height = max_y - min_y
        perimeter = 2 * (width + height)

        # Keep rectangle with minimum perimeter
        if perimeter < min_perimeter:
            min_perimeter = perimeter

            # Create rectangle corners in rotated coordinates
            rect_rotated = np.array(
                [[min_x, min_y], [max_x, min_y], [max_x, max_y], [min_x, max_y]]
            )

            # Rotate back to original coordinates
            inverse_rotation = np.array([[cos_angle, sin_angle], [-sin_angle, cos_angle]])

            best_rectangle = rect_rotated @ inverse_rotation.T
            best_angle = np.degrees(edge_angle)

    return best_rectangle, best_angle


def get_mbr_with_orientation(polygon: Polygon, preferred_angle_degrees: float) -> np.ndarray:
    """
    Get minimum bounding rectangle aligned with a preferred orientation.

    Args:
        polygon: Input polygon
        preferred_angle_degrees: Preferred orientation angle in degrees

    Returns:
        Rectangle coordinates (4, 2) array
    """
    # Get polygon coordinates
    coords = np.array(polygon.exterior.coords[:-1])

    # Convert angle to radians
    angle_rad = np.radians(preferred_angle_degrees)

    # Rotate polygon to align with preferred angle
    cos_angle = np.cos(-angle_rad)
    sin_angle = np.sin(-angle_rad)

    rotation_matrix = np.array([[cos_angle, -sin_angle], [sin_angle, cos_angle]])

    rotated_coords = coords @ rotation_matrix.T

    # Get axis-aligned bounding box
    min_x = np.min(rotated_coords[:, 0])
    max_x = np.max(rotated_coords[:, 0])
    min_y = np.min(rotated_coords[:, 1])
    max_y = np.max(rotated_coords[:, 1])

    # Create rectangle in rotated coordinates
    rect_rotated = np.array([[min_x, min_y], [max_x, min_y], [max_x, max_y], [min_x, max_y]])

    # Rotate back
    inverse_rotation = np.array([[cos_angle, sin_angle], [-sin_angle, cos_angle]])

    rectangle = rect_rotated @ inverse_rotation.T

    return rectangle


def get_mbr_dimensions(rectangle: np.ndarray) -> Tuple[float, float]:
    """
    Get width and height of MBR.

    Args:
        rectangle: (4, 2) array of rectangle corners

    Returns:
        (width, height) tuple
    """
    # Calculate edge lengths
    edge1_length = np.linalg.norm(rectangle[1] - rectangle[0])
    edge2_length = np.linalg.norm(rectangle[2] - rectangle[1])

    return (edge1_length, edge2_length)


def get_mbr_long_edge_direction(rectangle: np.ndarray) -> float:
    """
    Get direction angle of the longer edge of MBR.

    Args:
        rectangle: (4, 2) array of rectangle corners

    Returns:
        Angle in degrees
    """
    # Calculate edge vectors
    edge1 = rectangle[1] - rectangle[0]
    edge2 = rectangle[2] - rectangle[1]

    # Determine longer edge
    edge1_length = np.linalg.norm(edge1)
    edge2_length = np.linalg.norm(edge2)

    long_edge = edge1 if edge1_length >= edge2_length else edge2

    # Calculate angle
    angle_rad = np.arctan2(long_edge[1], long_edge[0])
    angle_deg = np.degrees(angle_rad)

    return angle_deg
