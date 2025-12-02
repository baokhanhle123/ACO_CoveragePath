"""
Tests for path generation from ACO solution (Stage 3).

Tests:
- Segment distance calculation
- Block track path generation
- Transition segment creation
- Working segment creation
- Complete path generation from solution
- Path statistics
"""

import pytest

from src.data.block import Block, BlockNode
from src.data.track import Track
from src.optimization.aco import Solution
from src.optimization.path_generation import (
    PathPlan,
    PathSegment,
    calculate_segment_distance,
    check_connection_crosses_obstacle,
    create_transition_segment,
    create_working_segment,
    create_working_segments,
    find_connectable_track_groups,
    generate_path_from_solution,
    get_block_tracks_path,
    get_path_statistics,
)
from shapely.geometry import Polygon


class TestSegmentDistance:
    """Test distance calculation for path segments."""

    def test_distance_zero_waypoints(self):
        """Test distance with no waypoints."""
        waypoints = []
        distance = calculate_segment_distance(waypoints)
        assert distance == 0.0

    def test_distance_single_waypoint(self):
        """Test distance with single waypoint."""
        waypoints = [(0.0, 0.0)]
        distance = calculate_segment_distance(waypoints)
        assert distance == 0.0

    def test_distance_straight_line(self):
        """Test distance along straight line."""
        waypoints = [(0.0, 0.0), (10.0, 0.0)]
        distance = calculate_segment_distance(waypoints)
        assert distance == 10.0

    def test_distance_multiple_segments(self):
        """Test distance with multiple segments."""
        # Right triangle: 3-4-5
        waypoints = [(0.0, 0.0), (3.0, 0.0), (3.0, 4.0)]
        distance = calculate_segment_distance(waypoints)
        assert distance == 7.0  # 3 + 4

    def test_distance_complex_path(self):
        """Test distance with complex path."""
        waypoints = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        distance = calculate_segment_distance(waypoints)
        assert distance == 30.0  # 10 + 10 + 10


class TestBlockTracksPath:
    """Test block tracks path generation."""

    def test_simple_block_forward(self):
        """Test forward traversal of simple block."""
        block = Block(
            block_id=0,
            boundary=[(0, 0), (10, 0), (10, 10), (0, 10)],
            tracks=[
                Track(start=(0, 2), end=(10, 2), index=0),
                Track(start=(0, 5), end=(10, 5), index=1),
            ],
        )

        nodes = block.create_entry_exit_nodes(start_index=0)
        entry_node = nodes[0]  # first_start
        exit_node = nodes[3]  # last_end

        waypoints = get_block_tracks_path(block, entry_node, exit_node)

        # Should have waypoints for traversing both tracks
        assert len(waypoints) > 0
        # First waypoint should be at start of first track
        assert waypoints[0] == (0, 2)
        # Last waypoint should be at end of last track
        assert waypoints[-1] == (0, 5)

    def test_block_with_single_track(self):
        """Test block with single track."""
        block = Block(
            block_id=0,
            boundary=[(0, 0), (10, 0), (10, 10), (0, 10)],
            tracks=[Track(start=(0, 5), end=(10, 5), index=0)],
        )

        nodes = block.create_entry_exit_nodes(start_index=0)
        entry_node = nodes[0]
        exit_node = nodes[3]

        waypoints = get_block_tracks_path(block, entry_node, exit_node)

        # Should traverse the single track
        assert len(waypoints) == 2
        assert waypoints[0] == (0, 5)
        assert waypoints[1] == (10, 5)


class TestTransitionSegment:
    """Test transition segment creation."""

    def test_simple_transition(self):
        """Test simple transition between two nodes."""
        node1 = BlockNode(position=(0.0, 0.0), block_id=0, node_type="first_end", index=0)
        node2 = BlockNode(position=(10.0, 0.0), block_id=1, node_type="first_start", index=4)

        segment = create_transition_segment(node1, node2)

        assert segment.segment_type == "transition"
        assert segment.block_id == -1
        assert len(segment.waypoints) == 2
        assert segment.waypoints[0] == (0.0, 0.0)
        assert segment.waypoints[1] == (10.0, 0.0)
        assert segment.distance == 10.0

    def test_diagonal_transition(self):
        """Test diagonal transition."""
        node1 = BlockNode(position=(0.0, 0.0), block_id=0, node_type="first_end", index=0)
        node2 = BlockNode(position=(3.0, 4.0), block_id=1, node_type="first_start", index=4)

        segment = create_transition_segment(node1, node2)

        assert segment.segment_type == "transition"
        assert segment.distance == 5.0  # 3-4-5 triangle


class TestWorkingSegment:
    """Test working segment creation."""

    def test_simple_working_segment(self):
        """Test working segment for simple block."""
        block = Block(
            block_id=0,
            boundary=[(0, 0), (10, 0), (10, 10), (0, 10)],
            tracks=[Track(start=(0, 5), end=(10, 5), index=0)],
        )

        nodes = block.create_entry_exit_nodes(start_index=0)
        entry_node = nodes[0]
        exit_node = nodes[3]

        segment = create_working_segment(block, entry_node, exit_node)

        assert segment.segment_type == "working"
        assert segment.block_id == 0
        assert len(segment.waypoints) >= 3  # entry + track points + exit
        assert segment.distance > 0


class TestPathGeneration:
    """Test complete path generation from solution."""

    def setup_method(self):
        """Set up test blocks and solution."""
        # Create 2 simple blocks
        self.block1 = Block(
            block_id=0,
            boundary=[(0, 0), (10, 0), (10, 10), (0, 10)],
            tracks=[Track(start=(0, 5), end=(10, 5), index=0)],
        )
        self.block2 = Block(
            block_id=1,
            boundary=[(20, 0), (30, 0), (30, 10), (20, 10)],
            tracks=[Track(start=(20, 5), end=(30, 5), index=0)],
        )

        self.blocks = [self.block1, self.block2]

        # Create nodes
        self.nodes1 = self.block1.create_entry_exit_nodes(start_index=0)
        self.nodes2 = self.block2.create_entry_exit_nodes(start_index=4)
        self.nodes = self.nodes1 + self.nodes2

    def test_path_generation_two_blocks(self):
        """Test path generation for two blocks."""
        # Create solution: block 0 then block 1
        # Each block appears twice (entry and exit nodes)
        solution = Solution(
            path=[0, 3, 4, 7],  # first_start(0) -> last_end(3) -> first_start(4) -> last_end(7)
            cost=50.0,
            block_sequence=[0, 0, 1, 1],  # Each block appears twice
        )

        path_plan = generate_path_from_solution(solution, self.blocks, self.nodes)

        # Should have 3 segments: work block 0, transition, work block 1
        assert len(path_plan.segments) == 3
        assert path_plan.segments[0].segment_type == "working"
        assert path_plan.segments[1].segment_type == "transition"
        assert path_plan.segments[2].segment_type == "working"

        # Check block sequence
        assert path_plan.block_sequence == [0, 0, 1, 1]

        # Check distances
        assert path_plan.working_distance > 0
        assert path_plan.transition_distance > 0
        assert path_plan.total_distance == path_plan.working_distance + path_plan.transition_distance

    def test_path_generation_invalid_solution(self):
        """Test that invalid solution raises error."""
        # Invalid solution - missing block
        solution = Solution(
            path=[0, 3],
            cost=20.0,
            block_sequence=[0],
        )

        with pytest.raises(ValueError, match="not valid"):
            generate_path_from_solution(solution, self.blocks, self.nodes)

    def test_path_plan_waypoints(self):
        """Test getting all waypoints from path plan."""
        solution = Solution(
            path=[0, 3, 4, 7],
            cost=50.0,
            block_sequence=[0, 0, 1, 1],  # Each block appears twice
        )

        path_plan = generate_path_from_solution(solution, self.blocks, self.nodes)
        all_waypoints = path_plan.get_all_waypoints()

        # Should have multiple waypoints
        assert len(all_waypoints) > 0

        # First waypoint should be at entry of first block
        assert all_waypoints[0] == self.nodes[0].position


class TestPathStatistics:
    """Test path statistics calculation."""

    def setup_method(self):
        """Set up test path plan."""
        # Create simple path plan
        segments = [
            PathSegment(
                segment_type="working",
                waypoints=[(0, 0), (10, 0)],
                block_id=0,
                distance=10.0,
            ),
            PathSegment(
                segment_type="transition",
                waypoints=[(10, 0), (20, 0)],
                block_id=-1,
                distance=10.0,
            ),
            PathSegment(
                segment_type="working",
                waypoints=[(20, 0), (30, 0)],
                block_id=1,
                distance=10.0,
            ),
        ]

        self.path_plan = PathPlan(
            segments=segments,
            total_distance=30.0,
            working_distance=20.0,
            transition_distance=10.0,
            block_sequence=[0, 1],
        )

    def test_basic_statistics(self):
        """Test basic path statistics."""
        stats = get_path_statistics(self.path_plan)

        assert stats["total_distance"] == 30.0
        assert stats["working_distance"] == 20.0
        assert stats["transition_distance"] == 10.0
        assert stats["num_blocks"] == 2
        assert stats["num_segments"] == 3
        assert stats["num_working_segments"] == 2
        assert stats["num_transition_segments"] == 1

    def test_efficiency_calculation(self):
        """Test path efficiency calculation."""
        stats = get_path_statistics(self.path_plan)

        # Efficiency = working / total = 20/30 = 0.667
        assert abs(stats["efficiency"] - 0.6667) < 0.001

    def test_waypoint_count(self):
        """Test total waypoint count."""
        stats = get_path_statistics(self.path_plan)

        # 3 segments, 2 waypoints each = 6 total
        assert stats["total_waypoints"] == 6


class TestPathIntegration:
    """Integration tests for complete path generation pipeline."""

    def test_three_block_path(self):
        """Test path generation for three blocks."""
        # Create 3 blocks in a row
        blocks = [
            Block(
                block_id=i,
                boundary=[(i*15, 0), (i*15+10, 0), (i*15+10, 10), (i*15, 10)],
                tracks=[Track(start=(i*15, 5), end=(i*15+10, 5), index=0)],
            )
            for i in range(3)
        ]

        # Create nodes
        nodes = []
        for i, block in enumerate(blocks):
            nodes.extend(block.create_entry_exit_nodes(start_index=i*4))

        # Create solution visiting all three blocks (2 nodes per block)
        solution = Solution(
            path=[0, 3, 4, 7, 8, 11],  # Visit each block with valid pairs
            cost=100.0,
            block_sequence=[0, 0, 1, 1, 2, 2],  # Each block appears twice
        )

        path_plan = generate_path_from_solution(solution, blocks, nodes)

        # Should have 5 segments: work, trans, work, trans, work
        assert len(path_plan.segments) == 5
        assert path_plan.block_sequence == [0, 0, 1, 1, 2, 2]

        # All blocks covered
        working_blocks = {s.block_id for s in path_plan.segments if s.segment_type == "working"}
        assert working_blocks == {0, 1, 2}

        # Statistics should be consistent
        stats = get_path_statistics(path_plan)
        assert stats["num_blocks"] == 6  # block_sequence has 6 entries (2 per block)
        assert stats["num_working_segments"] == 3
        assert stats["num_transition_segments"] == 2


class TestObstacleAvoidance:
    """Test obstacle avoidance in path generation."""

    def test_check_connection_crosses_obstacle_no_crossing(self):
        """Test obstacle crossing detection - no crossing case."""
        obstacle = Polygon([(40, 30), (60, 30), (60, 50), (40, 50)])

        # Connection doesn't cross obstacle
        assert not check_connection_crosses_obstacle(
            (30, 40), (35, 40), [obstacle]
        )

    def test_check_connection_crosses_obstacle_crossing(self):
        """Test obstacle crossing detection - crossing case."""
        obstacle = Polygon([(40, 30), (60, 30), (60, 50), (40, 50)])

        # Connection crosses through obstacle
        assert check_connection_crosses_obstacle(
            (30, 40), (70, 40), [obstacle]
        )

    def test_check_connection_crosses_obstacle_no_obstacles(self):
        """Test obstacle crossing detection - no obstacles."""
        # No obstacles - should never cross
        assert not check_connection_crosses_obstacle(
            (30, 40), (70, 40), []
        )

    def test_check_connection_touches_obstacle(self):
        """Test obstacle crossing detection - just touching."""
        obstacle = Polygon([(40, 30), (60, 30), (60, 50), (40, 50)])

        # Line just touches edge (should not be flagged as crossing)
        assert not check_connection_crosses_obstacle(
            (30, 30), (35, 30), [obstacle]
        )

    def test_find_connectable_track_groups_no_obstacles(self):
        """Test track grouping with no obstacles - all tracks connectable."""
        tracks = [
            Track(start=(10, 40), end=(90, 40), index=0),
            Track(start=(10, 45), end=(90, 45), index=1),
            Track(start=(10, 50), end=(90, 50), index=2),
        ]

        groups = find_connectable_track_groups(tracks, True, True, [])

        # All tracks should be in one group
        assert len(groups) == 1
        assert groups[0] == [0, 1, 2]

    def test_find_connectable_track_groups_with_obstacle(self):
        """Test track grouping when obstacle separates tracks."""
        # Create tracks that are split by obstacle in the middle
        tracks = [
            Track(start=(10, 40), end=(35, 40), index=0),
            Track(start=(10, 45), end=(35, 45), index=1),  # Group 1
            Track(start=(65, 40), end=(90, 40), index=2),
            Track(start=(65, 45), end=(90, 45), index=3),  # Group 2
        ]
        obstacle = Polygon([(40, 30), (60, 30), (60, 50), (40, 50)])

        groups = find_connectable_track_groups(tracks, True, True, [obstacle])

        # Should have 2 groups
        assert len(groups) == 2
        assert groups[0] == [0, 1]
        assert groups[1] == [2, 3]

    def test_find_connectable_track_groups_reverse_direction(self):
        """Test track grouping with reverse traversal direction."""
        # Tracks separated by obstacle, but traversing in reverse
        tracks = [
            Track(start=(10, 40), end=(35, 40), index=0),
            Track(start=(10, 45), end=(35, 45), index=1),
            Track(start=(65, 40), end=(90, 40), index=2),
            Track(start=(65, 45), end=(90, 45), index=3),
        ]
        obstacle = Polygon([(40, 30), (60, 30), (60, 50), (40, 50)])

        # entry_is_start=False, exit_is_end=False (reverse direction)
        groups = find_connectable_track_groups(tracks, False, False, [obstacle])

        # Should still have 2 groups
        assert len(groups) == 2
        assert groups[0] == [0, 1]
        assert groups[1] == [2, 3]

    def test_create_working_segments_no_obstacles(self):
        """Test create_working_segments with no obstacles - single segment."""
        block = Block(
            block_id=0,
            boundary=[(0, 0), (100, 0), (100, 60), (0, 60)],
            tracks=[
                Track(start=(10, 40), end=(90, 40), index=0),
                Track(start=(10, 45), end=(90, 45), index=1),
            ],
        )

        nodes = block.create_entry_exit_nodes(start_index=0)
        entry_node = nodes[0]  # first_start
        exit_node = nodes[3]   # last_end

        segments = create_working_segments(block, entry_node, exit_node, obstacles=[])

        # Should create single working segment (no obstacles to split)
        assert len(segments) == 1
        assert segments[0].segment_type == "working"
        assert segments[0].block_id == 0

    def test_create_working_segments_with_obstacle(self):
        """Test create_working_segments with obstacle splitting tracks."""
        # Block with tracks split by obstacle
        block = Block(
            block_id=0,
            boundary=[(0, 0), (100, 0), (100, 60), (0, 60)],
            tracks=[
                Track(start=(10, 40), end=(35, 40), index=0),
                Track(start=(10, 45), end=(35, 45), index=1),
                Track(start=(65, 40), end=(90, 40), index=2),
                Track(start=(65, 45), end=(90, 45), index=3),
            ],
        )

        nodes = block.create_entry_exit_nodes(start_index=0)
        entry_node = nodes[0]  # first_start
        exit_node = nodes[3]   # last_end

        obstacle = Polygon([(40, 30), (60, 30), (60, 50), (40, 50)])

        segments = create_working_segments(block, entry_node, exit_node, obstacles=[obstacle])

        # Should create multiple segments:
        # 1. Entry transition to first group
        # 2. Working segment for first group
        # 3. Transition between groups
        # 4. Working segment for second group
        # 5. Exit transition from last group
        assert len(segments) >= 3  # At least: entry trans, working, working

        # Should have working segments
        working_segments = [s for s in segments if s.segment_type == "working"]
        assert len(working_segments) >= 2  # At least 2 working segments (2 groups)

        # Should have transition segments
        transition_segments = [s for s in segments if s.segment_type == "transition"]
        assert len(transition_segments) >= 1  # At least 1 transition between groups

    def test_create_working_segments_empty_block(self):
        """Test create_working_segments with empty block (no tracks)."""
        block = Block(
            block_id=0,
            boundary=[(0, 0), (100, 0), (100, 60), (0, 60)],
            tracks=[],
        )

        # Create nodes manually since block.create_entry_exit_nodes requires tracks
        entry_node = BlockNode(
            position=(10, 30),
            block_id=0,
            node_type="first_start",
            index=0
        )
        exit_node = BlockNode(
            position=(90, 30),
            block_id=0,
            node_type="last_end",
            index=3
        )

        segments = create_working_segments(block, entry_node, exit_node, obstacles=[])

        # Should create single transition segment
        assert len(segments) == 1
        assert segments[0].segment_type == "transition"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
