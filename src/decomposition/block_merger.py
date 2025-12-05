"""
Block merging for boustrophedon decomposition.

Implements the block-merging part of the *second stage* in Zhou et al. 2014
([`10.1016/j.compag.2014.08.013`](http://dx.doi.org/10.1016/j.compag.2014.08.013)),
Section 2.3.2:

- Builds an adjacency graph between preliminary blocks (boustrophedon cells)
- Greedily merges adjacent blocks to reduce their total number
- Prioritizes merging narrow blocks first, in line with the discussion in
  Section 2.3.2 on eliminating narrow cells while preserving good geometry.

The goal is to reduce the number of blocks while maintaining:
1. Obstacle-free cells
2. Convex or near-convex shapes
3. Efficient coverage with parallel tracks
"""

from typing import List, Optional

from shapely.geometry import LineString, MultiLineString

from ..data.block import Block, BlockGraph


def build_block_adjacency_graph(blocks: List[Block]) -> BlockGraph:
    """
    Build adjacency graph for preliminary blocks.

    Two blocks are adjacent if they share a common edge that is exclusively shared
    (not shared with any other block), as specified in the paper.

    Args:
        blocks: List of preliminary blocks from decomposition

    Returns:
        BlockGraph with adjacency relationships

    Algorithm:
        1. Create BlockGraph with all blocks
        2. For each pair of blocks:
           a. Check if boundaries share an exclusive edge (not just touch at point)
           b. Add edge if adjacent with exclusive edge
    """
    # Create empty graph
    graph = BlockGraph()

    # Add all blocks
    for block in blocks:
        graph.add_block(block)

    # Check all pairs for adjacency with exclusive edges
    for i in range(len(blocks)):
        for j in range(i + 1, len(blocks)):
            if check_blocks_have_exclusive_edge(blocks[i], blocks[j], blocks):
                graph.add_edge(blocks[i].block_id, blocks[j].block_id)

    return graph


def check_blocks_adjacent(block1: Block, block2: Block, threshold: float = 0.01) -> bool:
    """
    Check if two blocks are adjacent (share a common edge).

    Args:
        block1: First block
        block2: Second block
        threshold: Minimum shared boundary length to consider adjacent

    Returns:
        True if blocks share an edge of length > threshold
    """
    # Get polygon boundaries as LineStrings
    boundary1 = block1.polygon.exterior
    boundary2 = block2.polygon.exterior

    # Get intersection
    intersection = boundary1.intersection(boundary2)

    # Check if intersection is a line (not just a point)
    if intersection.is_empty:
        return False

    # Calculate total intersection length
    total_length = 0.0

    if isinstance(intersection, LineString):
        total_length = intersection.length
    elif isinstance(intersection, MultiLineString):
        # Multiple shared edges
        total_length = sum(line.length for line in intersection.geoms)
    # else: Point or other geometry type → not adjacent

    return total_length > threshold


def check_blocks_have_exclusive_edge(
    block1: Block, block2: Block, all_blocks: List[Block], threshold: float = 0.01
) -> bool:
    """
    Check if two blocks share a common edge that is exclusively shared (not shared with any other block).

    According to the paper, "The merging requirement is that two connected blocks in the graph
    have a common edge." The common edge must be shared exclusively by the two blocks.

    Args:
        block1: First block
        block2: Second block
        all_blocks: List of all blocks (to check for exclusivity)
        threshold: Minimum shared boundary length to consider adjacent

    Returns:
        True if blocks share an exclusive common edge (not shared with any other block)
    """
    # First check if blocks are adjacent at all
    if not check_blocks_adjacent(block1, block2, threshold):
        return False

    # Get polygon boundaries as LineStrings
    boundary1 = block1.polygon.exterior
    boundary2 = block2.polygon.exterior

    # Get intersection (shared edge segments)
    intersection = boundary1.intersection(boundary2)

    if intersection.is_empty:
        return False

    # Extract shared edge segments
    shared_segments = []
    if isinstance(intersection, LineString):
        shared_segments = [intersection]
    elif isinstance(intersection, MultiLineString):
        shared_segments = list(intersection.geoms)
    else:
        # Point or other geometry type → not a valid edge
        return False

    # Check each shared segment to ensure it's not shared with any other block
    for shared_segment in shared_segments:
        # Check if this segment is also shared with any other block
        for other_block in all_blocks:
            # Skip the two blocks we're checking
            if other_block.block_id == block1.block_id or other_block.block_id == block2.block_id:
                continue

            # Check if other block also intersects with this shared segment
            other_boundary = other_block.polygon.exterior
            other_intersection = other_boundary.intersection(shared_segment)

            # If other block also shares this segment (or part of it), it's not exclusive
            if not other_intersection.is_empty:
                # Check if the intersection has meaningful length (not just a point)
                if isinstance(other_intersection, LineString):
                    if other_intersection.length > threshold:
                        return False  # Segment is shared with another block
                elif isinstance(other_intersection, MultiLineString):
                    total_other_length = sum(line.length for line in other_intersection.geoms)
                    if total_other_length > threshold:
                        return False  # Segment is shared with another block
                elif hasattr(other_intersection, 'length') and other_intersection.length > threshold:
                    return False  # Segment is shared with another block

            # Also check if other block shares an edge with block2 on the same "side"
            # This handles cases where one block's edge is split into multiple segments
            # shared by different blocks (e.g., B7's left edge shared by both B4 and B5)
            # If block2 shares edges with both block1 and other_block, and those edges
            # are on the same side of block2, then block1 and block2 don't have an exclusive edge
            other_shared_with_block2 = block2.polygon.exterior.intersection(other_boundary)
            if not other_shared_with_block2.is_empty:
                # Check if the shared segments are on the same side of block2
                # by checking if they're collinear or adjacent
                other_segments = []
                if isinstance(other_shared_with_block2, LineString):
                    other_segments = [other_shared_with_block2]
                elif isinstance(other_shared_with_block2, MultiLineString):
                    other_segments = list(other_shared_with_block2.geoms)
                
                for other_seg in other_segments:
                    if other_seg.length > threshold:
                        # Check if this segment is collinear or adjacent to shared_segment
                        # Two segments are on the same edge if they're collinear and close
                        # or if they share an endpoint
                        other_coords = list(other_seg.coords)
                        shared_coords = list(shared_segment.coords)
                        if other_coords and shared_coords:
                            # Check if segments share an endpoint (adjacent)
                            if (other_coords[0] == shared_coords[-1] or 
                                other_coords[-1] == shared_coords[0] or
                                other_coords[0] == shared_coords[0] or
                                other_coords[-1] == shared_coords[-1]):
                                # Segments are adjacent - same edge, not exclusive
                                return False
                            # Check if segments are collinear (same line, different parts)
                            # Simple heuristic: if both are vertical/horizontal and on same coordinate
                            if (len(other_coords) >= 2 and len(shared_coords) >= 2):
                                # Check if both segments are on the same vertical or horizontal line
                                other_is_vertical = abs(other_coords[0][0] - other_coords[-1][0]) < 1e-6
                                other_is_horizontal = abs(other_coords[0][1] - other_coords[-1][1]) < 1e-6
                                shared_is_vertical = abs(shared_coords[0][0] - shared_coords[-1][0]) < 1e-6
                                shared_is_horizontal = abs(shared_coords[0][1] - shared_coords[-1][1]) < 1e-6
                                
                                if other_is_vertical and shared_is_vertical:
                                    # Both vertical - check if same x coordinate
                                    if abs(other_coords[0][0] - shared_coords[0][0]) < 1e-6:
                                        # Same vertical line - not exclusive
                                        return False
                                elif other_is_horizontal and shared_is_horizontal:
                                    # Both horizontal - check if same y coordinate
                                    if abs(other_coords[0][1] - shared_coords[0][1]) < 1e-6:
                                        # Same horizontal line - not exclusive
                                        return False

    # All shared segments are exclusive to block1 and block2
    return True


def calculate_merge_cost(block1: Block, block2: Block) -> float:
    """
    Calculate cost/penalty of merging two blocks.

    Lower cost = better merge candidate.

    Cost factors:
    - Shape irregularity after merge (convexity)
    - Area efficiency
    - Track uniformity

    Args:
        block1: First block
        block2: Second block

    Returns:
        Merge cost (lower is better)
    """
    # Merge the blocks to evaluate the result
    merged_poly = block1.polygon.union(block2.polygon)

    if not merged_poly.is_valid:
        merged_poly = merged_poly.buffer(0)

    # Cost factor 1: Convexity (how much area is lost to convex hull)
    # Lower convexity ratio = more complex shape = higher cost
    convex_hull = merged_poly.convex_hull
    convexity_ratio = merged_poly.area / convex_hull.area if convex_hull.area > 0 else 0
    convexity_cost = 1.0 - convexity_ratio  # 0 = perfectly convex, 1 = very concave

    # Cost factor 2: Area imbalance
    # Prefer merging blocks of similar size
    total_area = block1.area + block2.area
    if total_area > 0:
        area_ratio = min(block1.area, block2.area) / max(block1.area, block2.area)
    else:
        area_ratio = 1.0
    area_cost = 1.0 - area_ratio  # 0 = equal sizes, 1 = very different

    # Cost factor 3: Perimeter (simpler shapes have lower perimeter/area ratio)
    perimeter_area_ratio = merged_poly.length / merged_poly.area if merged_poly.area > 0 else 0
    # Normalize by comparing to a square of same area
    square_perimeter_area = 4 / (merged_poly.area ** 0.5) if merged_poly.area > 0 else 1
    if square_perimeter_area > 0:
        shape_complexity = perimeter_area_ratio / square_perimeter_area
    else:
        shape_complexity = 1
    complexity_cost = min(shape_complexity - 1.0, 1.0)  # 0 = square-like, higher = more complex

    # Weighted combination (prefer convexity and simplicity)
    total_cost = 0.5 * convexity_cost + 0.3 * area_cost + 0.2 * complexity_cost

    return total_cost


def merge_two_blocks(block1: Block, block2: Block, new_block_id: int) -> Block:
    """
    Merge two adjacent blocks into a single block.

    Args:
        block1: First block
        block2: Second block
        new_block_id: ID for merged block

    Returns:
        New merged Block object

    Algorithm:
        1. Union the two block polygons
        2. Simplify boundary if needed
        3. Combine tracks from both blocks
        4. Create new Block with merged data
    """
    # Union the two polygons
    merged_polygon = block1.polygon.union(block2.polygon)

    # Fix any geometry issues
    if not merged_polygon.is_valid:
        merged_polygon = merged_polygon.buffer(0)

    # Get boundary coordinates
    boundary_coords = list(merged_polygon.exterior.coords[:-1])

    # Combine tracks (will be regenerated later anyway)
    merged_tracks = block1.tracks + block2.tracks

    # Create merged block
    merged_block = Block(block_id=new_block_id, boundary=boundary_coords, tracks=merged_tracks)

    return merged_block


def greedy_block_merging(
    block_graph: BlockGraph, min_block_area: Optional[float] = None, verbose: bool = False
) -> BlockGraph:
    """
    Perform greedy block merging to reduce total number of blocks.

    Two-phase strategy:
    Phase 1: Merge small blocks (area < min_block_area) to eliminate narrow cells
    Phase 2: Merge any adjacent blocks (regardless of size) to reduce total count

    Strategy from paper:
    1. Start with smallest/narrowest blocks
    2. Merge with best adjacent neighbor
    3. Update adjacency graph
    4. Repeat until no beneficial merges remain

    Args:
        block_graph: Initial block adjacency graph
        min_block_area: Optional minimum desired block area
        verbose: If True, print merging details

    Returns:
        Updated BlockGraph with merged blocks

    Termination conditions:
    - Phase 1: All blocks meet minimum area requirement
    - Phase 2: No adjacent blocks remain to merge
    """
    if min_block_area is None:
        min_block_area = 0  # No minimum constraint

    max_iterations = 1000  # Safety limit
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        # Phase 1: Find smallest block below threshold
        smallest_block = None
        smallest_area = float('inf')

        for block in block_graph.blocks:
            if block.area < min_block_area and block.area < smallest_area:
                # Check if it has neighbors to merge with
                neighbors = block_graph.get_adjacent_blocks(block.block_id)
                if neighbors:
                    smallest_block = block
                    smallest_area = block.area

        # Phase 2: If no small blocks found, merge any adjacent blocks
        # to further reduce total count (prioritize smaller blocks first)
        if smallest_block is None:
            # Find smallest block (any size) that has adjacent neighbors
            for block in block_graph.blocks:
                neighbors = block_graph.get_adjacent_blocks(block.block_id)
                if neighbors and block.area < smallest_area:
                    smallest_block = block
                    smallest_area = block.area

            # If no blocks with neighbors found, stop merging
            if smallest_block is None:
                break

        # Get adjacent blocks
        neighbor_ids = block_graph.get_adjacent_blocks(smallest_block.block_id)

        if not neighbor_ids:
            # No neighbors to merge with, skip this block
            # Keep it in the graph (it will remain in final result) but skip merging
            # This can happen if all its neighbors were already merged
            continue

        # Find best neighbor to merge with (lowest cost)
        best_neighbor = None
        best_cost = float('inf')

        for neighbor_id in neighbor_ids:
            neighbor = block_graph.get_block_by_id(neighbor_id)
            if neighbor is None:
                continue

            cost = calculate_merge_cost(smallest_block, neighbor)
            if cost < best_cost:
                best_cost = cost
                best_neighbor = neighbor

        if best_neighbor is None:
            break

        # Merge the two blocks (keep the smaller ID to maintain numbering continuity)
        new_block_id = min(smallest_block.block_id, best_neighbor.block_id)

        if verbose:
            print(f"  Merging B{smallest_block.block_id} (area={smallest_block.area:.2f}) "
                  f"+ B{best_neighbor.block_id} (area={best_neighbor.area:.2f}) "
                  f"→ B{new_block_id} (cost={best_cost:.3f})")

        merged_block = merge_two_blocks(smallest_block, best_neighbor, new_block_id)

        # Update graph: remove old blocks, add merged block
        block_graph.blocks = [
            b for b in block_graph.blocks
            if b.block_id != smallest_block.block_id and b.block_id != best_neighbor.block_id
        ]
        block_graph.blocks.append(merged_block)

        # Update adjacency: collect all neighbors of both old blocks
        old_neighbors = set()
        if smallest_block.block_id in block_graph.adjacency:
            old_neighbors.update(block_graph.adjacency[smallest_block.block_id])
        if best_neighbor.block_id in block_graph.adjacency:
            old_neighbors.update(block_graph.adjacency[best_neighbor.block_id])

        # Remove old adjacency entries
        if smallest_block.block_id in block_graph.adjacency:
            del block_graph.adjacency[smallest_block.block_id]
        if best_neighbor.block_id in block_graph.adjacency:
            del block_graph.adjacency[best_neighbor.block_id]

        # Remove references to old blocks from other blocks' adjacency lists
        for block_id in block_graph.adjacency:
            block_graph.adjacency[block_id] = [
                bid for bid in block_graph.adjacency[block_id]
                if bid != smallest_block.block_id and bid != best_neighbor.block_id
            ]

        # Add new block to adjacency
        block_graph.adjacency[new_block_id] = []

        # Re-check adjacency with all old neighbors using exclusive edge check
        # Need to pass all remaining blocks to check exclusivity
        remaining_blocks = block_graph.blocks
        for neighbor_id in old_neighbors:
            if neighbor_id == smallest_block.block_id or neighbor_id == best_neighbor.block_id:
                continue
            neighbor_block = block_graph.get_block_by_id(neighbor_id)
            if neighbor_block and check_blocks_have_exclusive_edge(
                merged_block, neighbor_block, remaining_blocks
            ):
                block_graph.add_edge(new_block_id, neighbor_id)

    return block_graph


def merge_blocks_by_criteria(
    blocks: List[Block],
    operating_width: float,
    min_block_width: Optional[float] = None,
) -> List[Block]:
    """
    High-level function to merge preliminary blocks.

    Wrapper around greedy merging with standard criteria.

    Args:
        blocks: Preliminary blocks from boustrophedon decomposition
        operating_width: Operating width (used for minimum size criteria)
        min_block_width: Minimum acceptable block width (default: 3 * operating_width)

    Returns:
        List of merged blocks with consecutive IDs (0, 1, 2, ...)
    """
    if not blocks:
        return []

    # Default minimum: blocks should fit at least 3 tracks
    if min_block_width is None:
        min_block_width = 3 * operating_width

    min_area = min_block_width * operating_width  # Rough minimum area

    # Build adjacency graph
    graph = build_block_adjacency_graph(blocks)

    # Perform greedy merging (verbose to show merging process)
    merged_graph = greedy_block_merging(graph, min_block_area=min_area, verbose=True)

    # Renumber blocks consecutively (0, 1, 2, ...) to match paper's presentation
    # This makes the result cleaner and easier to understand
    final_blocks = merged_graph.blocks
    final_blocks.sort(key=lambda b: b.block_id)  # Sort by original ID first

    for new_id, block in enumerate(final_blocks):
        block.block_id = new_id

    return final_blocks


def get_merging_statistics(
    initial_blocks: List[Block], merged_blocks: List[Block]
) -> dict:
    """
    Calculate statistics about block merging.

    Args:
        initial_blocks: Blocks before merging
        merged_blocks: Blocks after merging

    Returns:
        Dictionary with merging statistics
    """
    return {
        "initial_count": len(initial_blocks),
        "final_count": len(merged_blocks),
        "reduction": len(initial_blocks) - len(merged_blocks),
        "reduction_pct": (
            100 * (len(initial_blocks) - len(merged_blocks)) / len(initial_blocks)
            if initial_blocks
            else 0
        ),
        "avg_initial_area": (
            sum(b.area for b in initial_blocks) / len(initial_blocks) if initial_blocks else 0
        ),
        "avg_final_area": (
            sum(b.area for b in merged_blocks) / len(merged_blocks) if merged_blocks else 0
        ),
    }
