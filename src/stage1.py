"""
Stage 1 pipeline: geometric representation, headlands, obstacle handling,
and initial track generation.

Implements the methodology described in Section 2.2 ("First stage") of
Zhou et al. 2014, *Agricultural operations planning in fields with
multiple obstacle areas* [`10.1016/j.compag.2014.08.013`].

High-level steps (see also paper, Sec. 2.1–2.2):
    1. Represent the field boundary and in-field obstacles as polygons.
    2. Generate a preliminary field headland (ignoring obstacle types)
       to obtain a first inner boundary.
    3. Classify obstacles into Types A–D:
       - Type A: small obstacles (ignored).
       - Type B: intersect the inner boundary (incorporated into
                 the field headland).
       - Type C: obstacles in close proximity (merged into an MBP).
       - Type D: obstacles requiring decomposition (standalone or
                 merged Type C).
    4. Regenerate the field headland with Type B obstacles incorporated
       into the inner boundary.
    5. Generate parallel field-work tracks to cover the field body,
       using only the inner boundary (obstacles ignored here, as in
       the paper's Stage 1).
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

from shapely.geometry import Polygon

from .data.field import Field, FieldParameters
from .data.obstacle import Obstacle
from .data.track import Track
from .geometry import (
    HeadlandResult,
    generate_field_headland,
    generate_obstacle_headland,
    generate_parallel_tracks,
)
from .obstacles.classifier import (
    classify_all_obstacles,
    get_type_b_obstacles,
    get_type_d_obstacles,
)


@dataclass
class Stage1Result:
    """
    Container for all geometric outputs of Stage 1.

    Attributes:
        field: Original field definition.
        params: Planning parameters (w, h, θ, thresholds, etc.).
        preliminary_headland: Headland generated before obstacle
            classification (used to detect Type B obstacles).
        classified_obstacles: All non-Type-A obstacles with their
            assigned types and any merge information.
        type_b_obstacles: Convenience subset of Type B obstacles.
        type_d_obstacles: Convenience subset of Type D obstacles
            (including merged Type C clusters).
        type_c_clusters: Indices of original obstacles that formed
            Type C proximity clusters (derived from merged Type D).
        field_headland: Final field headland with Type B obstacles
            incorporated into the inner boundary.
        obstacle_headlands: Headlands generated around Type D
            obstacles (used mainly for visualization / later stages).
        tracks: Parallel field-work tracks covering the field body
            (inner boundary of `field_headland`), ignoring obstacles.
    """

    field: Field
    params: FieldParameters
    preliminary_headland: HeadlandResult
    classified_obstacles: List[Obstacle]
    type_b_obstacles: List[Obstacle]
    type_d_obstacles: List[Obstacle]
    type_c_clusters: List[List[int]]
    field_headland: HeadlandResult
    obstacle_headlands: List[Tuple[Obstacle, HeadlandResult]]
    tracks: List[Track]


def run_stage1_pipeline(field: Field, params: FieldParameters) -> Stage1Result:
    """
    Execute the complete Stage 1 pipeline for a given field.

    This function mirrors the textual description of the first stage in
    Zhou et al. 2014 (Sec. 2.2), and serves as a single entry point for
    simulations, tests, and visualizations.

    Args:
        field: Field geometry with obstacles.
        params: Planning parameters, including operating width (w),
            number of headland passes (h), driving direction (θ),
            and obstacle threshold τ.

    Returns:
        Stage1Result with all intermediate and final geometrical objects.
    """
    # ------------------------------------------------------------------
    # Step 1–2: Preliminary field headland (before obstacle types)
    # ------------------------------------------------------------------
    preliminary_headland = generate_field_headland(
        field_boundary=field.boundary_polygon,
        operating_width=params.operating_width,
        num_passes=params.num_headland_passes,
    )

    # ------------------------------------------------------------------
    # Step 3: Obstacle classification (Types A–D)
    # ------------------------------------------------------------------
    classified_obstacles = classify_all_obstacles(
        obstacle_boundaries=field.obstacles,
        field_inner_boundary=preliminary_headland.inner_boundary,
        driving_direction_degrees=params.driving_direction,
        operating_width=params.operating_width,
        threshold=params.obstacle_threshold,
    )

    type_b_obstacles = get_type_b_obstacles(classified_obstacles)
    type_d_obstacles = get_type_d_obstacles(classified_obstacles)

    # Derive Type C clusters from merged Type D obstacles
    type_c_clusters: List[List[int]] = []
    for obs in type_d_obstacles:
        if obs.is_merged() and obs.merged_from is not None:
            type_c_clusters.append(list(obs.merged_from))

    # ------------------------------------------------------------------
    # Step 4: Regenerate field headland with Type B obstacles incorporated
    # ------------------------------------------------------------------
    type_b_polygons: List[Polygon] = [obs.polygon for obs in type_b_obstacles]

    field_headland = generate_field_headland(
        field_boundary=field.boundary_polygon,
        operating_width=params.operating_width,
        num_passes=params.num_headland_passes,
        type_b_obstacles=type_b_polygons if type_b_polygons else None,
    )

    # ------------------------------------------------------------------
    # Step 5: Generate obstacle headlands around Type D obstacles
    # (primarily for visualization and for later decomposition stages).
    # ------------------------------------------------------------------
    obstacle_headlands: List[Tuple[Obstacle, HeadlandResult]] = []
    for obs in type_d_obstacles:
        obs_headland = generate_obstacle_headland(
            obstacle_boundary=obs.polygon,
            operating_width=params.operating_width,
            num_passes=params.num_headland_passes,
        )
        if obs_headland is not None:
            obstacle_headlands.append((obs, obs_headland))

    # ------------------------------------------------------------------
    # Step 6: Generate parallel tracks on the field body.
    #
    # IMPORTANT: As in the paper's Stage 1, in-field obstacles are
    # ignored here – only the inner boundary of the (final) headland
    # is used. Obstacles are handled in decomposition (Stage 2).
    # ------------------------------------------------------------------
    tracks = generate_parallel_tracks(
        inner_boundary=field_headland.inner_boundary,
        driving_direction_degrees=params.driving_direction,
        operating_width=params.operating_width,
    )

    return Stage1Result(
        field=field,
        params=params,
        preliminary_headland=preliminary_headland,
        classified_obstacles=classified_obstacles,
        type_b_obstacles=type_b_obstacles,
        type_d_obstacles=type_d_obstacles,
        type_c_clusters=type_c_clusters,
        field_headland=field_headland,
        obstacle_headlands=obstacle_headlands,
        tracks=tracks,
    )


