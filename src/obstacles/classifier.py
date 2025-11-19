"""
Obstacle classification system.

Implements obstacle categorization from Zhou et al. 2014 (Section 2.2.2):
- Type A: Small obstacles (dimension < threshold τ perpendicular to driving direction)
- Type B: Obstacles intersecting with field inner boundary
- Type C: Obstacles in close proximity (distance < operating width)
- Type D: Standard obstacles requiring decomposition (remaining + merged Type C)
"""
from typing import List, Tuple, Optional, Set
import numpy as np
from shapely.geometry import Polygon
from scipy.spatial import ConvexHull

from ..data.obstacle import Obstacle, ObstacleType
from ..geometry.polygon import minimum_distance_between_polygons, polygon_union


def classify_obstacle_type_a(
    obstacle_polygon: Polygon,
    driving_direction_degrees: float,
    threshold: float
) -> bool:
    """
    Classify if obstacle is Type A (ignorable due to small size).

    Algorithm from paper:
    1. Generate minimum bounding box with edge parallel to driving direction
    2. Get dimension D_d perpendicular to driving direction
    3. If D_d < threshold τ: Type A

    Args:
        obstacle_polygon: Obstacle polygon
        driving_direction_degrees: Driving direction angle
        threshold: Classification threshold τ

    Returns:
        True if Type A, False otherwise
    """
    # Get obstacle coordinates
    coords = np.array(obstacle_polygon.exterior.coords[:-1])

    if len(coords) < 3:
        return True  # Degenerate obstacle

    # Rotate to align with driving direction
    angle_rad = np.radians(-driving_direction_degrees)
    cos_angle = np.cos(angle_rad)
    sin_angle = np.sin(angle_rad)

    rotation_matrix = np.array([
        [cos_angle, -sin_angle],
        [sin_angle, cos_angle]
    ])

    rotated_coords = coords @ rotation_matrix.T

    # Get bounding box in rotated coordinates
    min_x = np.min(rotated_coords[:, 0])
    max_x = np.max(rotated_coords[:, 0])
    min_y = np.min(rotated_coords[:, 1])
    max_y = np.max(rotated_coords[:, 1])

    # Dimension parallel to driving direction
    d_parallel = max_x - min_x

    # Dimension perpendicular to driving direction (D_d)
    d_perpendicular = max_y - min_y

    # Type A if perpendicular dimension < threshold
    return d_perpendicular < threshold


def classify_obstacle_type_b(
    obstacle_polygon: Polygon,
    field_inner_boundary: Polygon
) -> bool:
    """
    Classify if obstacle is Type B (intersecting with field inner boundary).

    Args:
        obstacle_polygon: Obstacle polygon
        field_inner_boundary: Inner boundary of field (after headland)

    Returns:
        True if Type B, False otherwise
    """
    # Check if obstacle boundary intersects with field inner boundary
    return obstacle_polygon.intersects(field_inner_boundary)


def find_type_c_clusters(
    obstacles: List[Polygon],
    operating_width: float
) -> List[List[int]]:
    """
    Find clusters of obstacles in close proximity (Type C).

    Algorithm:
    1. For each pair of obstacles, check if min_distance < operating_width
    2. Build connectivity graph
    3. Find connected components (clusters)

    Args:
        obstacles: List of obstacle polygons
        operating_width: Operating width threshold

    Returns:
        List of clusters, each cluster is a list of obstacle indices
    """
    n = len(obstacles)

    if n == 0:
        return []

    # Build adjacency list for obstacles within threshold distance
    adjacency = {i: [] for i in range(n)}

    for i in range(n):
        for j in range(i + 1, n):
            distance = minimum_distance_between_polygons(obstacles[i], obstacles[j])

            if distance < operating_width:
                adjacency[i].append(j)
                adjacency[j].append(i)

    # Find connected components using DFS
    visited = set()
    clusters = []

    def dfs(node: int, cluster: Set[int]):
        visited.add(node)
        cluster.add(node)
        for neighbor in adjacency[node]:
            if neighbor not in visited:
                dfs(neighbor, cluster)

    for i in range(n):
        if i not in visited:
            if adjacency[i]:  # Has neighbors (Type C)
                cluster = set()
                dfs(i, cluster)
                if len(cluster) > 1:  # Cluster of 2 or more
                    clusters.append(sorted(list(cluster)))

    return clusters


def merge_obstacles(obstacle_polygons: List[Polygon]) -> Polygon:
    """
    Merge multiple obstacles into minimal bounding polygon (MBP).

    Uses convex hull to create minimal bounding polygon.

    Args:
        obstacle_polygons: List of polygons to merge

    Returns:
        Merged polygon (convex hull)
    """
    if not obstacle_polygons:
        raise ValueError("Need at least one obstacle to merge")

    if len(obstacle_polygons) == 1:
        return obstacle_polygons[0]

    # Collect all coordinates
    all_coords = []
    for poly in obstacle_polygons:
        all_coords.extend(list(poly.exterior.coords[:-1]))

    coords_array = np.array(all_coords)

    # Compute convex hull
    try:
        hull = ConvexHull(coords_array)
        hull_coords = coords_array[hull.vertices]
        merged_polygon = Polygon(hull_coords)
    except Exception:
        # Fallback: use union
        merged_polygon = polygon_union(obstacle_polygons)
        if hasattr(merged_polygon, 'convex_hull'):
            merged_polygon = merged_polygon.convex_hull

    return merged_polygon


def classify_all_obstacles(
    obstacle_boundaries: List[List[Tuple[float, float]]],
    field_inner_boundary: Polygon,
    driving_direction_degrees: float,
    operating_width: float,
    threshold: float
) -> List[Obstacle]:
    """
    Classify all obstacles into types A, B, C, D.

    Processing order (as per paper):
    1. Type A: Small obstacles (ignored)
    2. Type B: Boundary-touching (merged into field headland)
    3. Type C: Close proximity (merged into MBP, then classified as Type D)
    4. Type D: All remaining obstacles

    Args:
        obstacle_boundaries: List of obstacle boundary coordinates
        field_inner_boundary: Field inner boundary polygon
        driving_direction_degrees: Driving direction
        operating_width: Operating width
        threshold: Type A classification threshold τ

    Returns:
        List of classified Obstacle objects (only Types B and D are kept)
    """
    if not obstacle_boundaries:
        return []

    # Convert to Polygons
    obstacle_polygons = [Polygon(obs) for obs in obstacle_boundaries]

    classified_obstacles = []
    type_d_candidates = []  # Indices of obstacles that might be Type D
    type_c_indices = set()  # Indices involved in Type C clusters

    # Step 1: Classify Type A (ignorable)
    for i, poly in enumerate(obstacle_polygons):
        is_type_a = classify_obstacle_type_a(poly, driving_direction_degrees, threshold)

        if is_type_a:
            # Type A obstacles are ignored (not added to result)
            continue

        # Not Type A, check Type B
        is_type_b = classify_obstacle_type_b(poly, field_inner_boundary)

        if is_type_b:
            # Type B obstacle
            obs = Obstacle(
                boundary=obstacle_boundaries[i],
                obstacle_type=ObstacleType.B,
                index=i
            )
            classified_obstacles.append(obs)
        else:
            # Candidate for Type C or D
            type_d_candidates.append(i)

    # Step 2: Find Type C clusters among Type D candidates
    candidate_polygons = [obstacle_polygons[i] for i in type_d_candidates]
    clusters = find_type_c_clusters(candidate_polygons, operating_width)

    # Create mapping from candidate index to original index
    candidate_to_original = {ci: type_d_candidates[ci] for ci in range(len(type_d_candidates))}

    # Step 3: Merge Type C clusters and mark as Type D
    for cluster in clusters:
        # Get original indices
        original_indices = [candidate_to_original[ci] for ci in cluster]
        type_c_indices.update(original_indices)

        # Merge obstacles in cluster
        cluster_polygons = [obstacle_polygons[i] for i in original_indices]
        merged_polygon = merge_obstacles(cluster_polygons)

        # Create merged obstacle (Type D, since merged Type C becomes Type D)
        merged_boundary = list(merged_polygon.exterior.coords[:-1])
        obs = Obstacle(
            boundary=merged_boundary,
            obstacle_type=ObstacleType.D,
            index=min(original_indices),  # Use smallest original index
            merged_from=original_indices
        )
        classified_obstacles.append(obs)

    # Step 4: Remaining Type D candidates (not in Type C clusters)
    for i in type_d_candidates:
        if i not in type_c_indices:
            obs = Obstacle(
                boundary=obstacle_boundaries[i],
                obstacle_type=ObstacleType.D,
                index=i
            )
            classified_obstacles.append(obs)

    return classified_obstacles


def get_type_d_obstacles(obstacles: List[Obstacle]) -> List[Obstacle]:
    """
    Filter only Type D obstacles (those requiring field decomposition).

    Args:
        obstacles: List of classified obstacles

    Returns:
        List containing only Type D obstacles
    """
    return [obs for obs in obstacles if obs.obstacle_type == ObstacleType.D]


def get_obstacle_statistics(obstacles: List[Obstacle]) -> dict:
    """
    Get statistics about classified obstacles.

    Args:
        obstacles: List of classified obstacles

    Returns:
        Dictionary with counts by type
    """
    stats = {
        "Type A": 0,
        "Type B": 0,
        "Type C": 0,
        "Type D": 0,
        "Merged": 0,
        "Total": len(obstacles)
    }

    for obs in obstacles:
        stats[f"Type {obs.obstacle_type.name}"] += 1
        if obs.is_merged():
            stats["Merged"] += 1

    return stats
