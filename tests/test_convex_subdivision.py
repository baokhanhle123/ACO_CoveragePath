"""
Unit tests for convex subdivision module.

Tests the convex_subdivision.py module that handles non-convex blocks
created by Type B obstacle holes during boustrophedon decomposition.
"""

import pytest
from shapely.geometry import Polygon

from src.data.block import Block
from src.decomposition.convex_subdivision import (
    create_vertical_slice,
    extract_hole_vertices,
    find_critical_x_coordinates,
    has_interior_holes,
    is_block_convex,
    subdivide_all_non_convex_blocks,
    subdivide_block_vertically,
    subdivide_non_convex_block,
)


class TestConvexityDetection:
    """Test convexity detection using convex hull ratio."""

    def test_convex_block(self):
        """Rectangle should be detected as convex."""
        # Create rectangular block (convex)
        boundary = [(0, 0), (10, 0), (10, 5), (0, 5)]
        block = Block(block_id=0, boundary=boundary)

        # Check convexity
        assert is_block_convex(block, threshold=0.99)

    def test_non_convex_block_l_shape(self):
        """L-shape should be detected as non-convex."""
        # Create L-shaped block (non-convex)
        boundary = [
            (0, 0),
            (10, 0),
            (10, 5),
            (5, 5),
            (5, 10),
            (0, 10),
        ]
        block = Block(block_id=0, boundary=boundary)

        # Check convexity
        assert not is_block_convex(block, threshold=0.99)

    def test_nearly_convex_block(self):
        """Block with slight indentation should fail strict threshold."""
        # Create block with small indentation
        boundary = [
            (0, 0),
            (10, 0),
            (10, 10),
            (5, 9.5),  # Small indentation
            (0, 10),
        ]
        block = Block(block_id=0, boundary=boundary)

        # With strict threshold (0.99), should be non-convex
        # Convex hull area = 100, actual area ≈ 97.5, ratio ≈ 0.975 < 0.99
        assert not is_block_convex(block, threshold=0.99)

        # With relaxed threshold (0.95), should be convex
        assert is_block_convex(block, threshold=0.95)

    def test_empty_block(self):
        """Empty block should be non-convex."""
        # Create empty block
        boundary = []
        block = Block(block_id=0, boundary=boundary)

        # Empty should be non-convex
        assert not is_block_convex(block, threshold=0.99)


class TestHoleDetection:
    """Test detection of interior holes in polygons."""

    def test_polygon_without_holes(self):
        """Simple polygon should have no holes."""
        # Create simple rectangle
        poly = Polygon([(0, 0), (10, 0), (10, 5), (0, 5)])

        # Should have no holes
        assert not has_interior_holes(poly)

    def test_polygon_with_hole(self):
        """Polygon with interior ring should be detected correctly."""
        # Create donut shape (polygon with hole)
        exterior = [(0, 0), (10, 0), (10, 10), (0, 10)]
        interior = [(3, 3), (7, 3), (7, 7), (3, 7)]
        poly = Polygon(exterior, [interior])

        # Should have hole
        assert has_interior_holes(poly)

    def test_polygon_with_multiple_holes(self):
        """Polygon with multiple holes should be detected."""
        # Create polygon with two holes
        exterior = [(0, 0), (20, 0), (20, 20), (0, 20)]
        hole1 = [(2, 2), (5, 2), (5, 5), (2, 5)]
        hole2 = [(10, 10), (15, 10), (15, 15), (10, 15)]
        poly = Polygon(exterior, [hole1, hole2])

        # Should have holes
        assert has_interior_holes(poly)


class TestHoleVertexExtraction:
    """Test extraction of vertices from interior holes."""

    def test_extract_single_hole_vertices(self):
        """Extract vertices from single hole."""
        # Create polygon with one hole
        exterior = [(0, 0), (10, 0), (10, 10), (0, 10)]
        interior = [(3, 3), (7, 3), (7, 7), (3, 7)]
        poly = Polygon(exterior, [interior])

        # Extract hole vertices
        vertices = extract_hole_vertices(poly)

        # Should have 4 vertices (excluding duplicate last point)
        assert len(vertices) == 4
        assert (3, 3) in vertices
        assert (7, 3) in vertices
        assert (7, 7) in vertices
        assert (3, 7) in vertices

    def test_extract_multiple_holes_vertices(self):
        """Extract vertices from multiple holes."""
        # Create polygon with two holes
        exterior = [(0, 0), (20, 0), (20, 20), (0, 20)]
        hole1 = [(2, 2), (5, 2), (5, 5), (2, 5)]
        hole2 = [(10, 10), (15, 10), (15, 15), (10, 15)]
        poly = Polygon(exterior, [hole1, hole2])

        # Extract hole vertices
        vertices = extract_hole_vertices(poly)

        # Should have 8 vertices total (4 from each hole)
        assert len(vertices) == 8

    def test_extract_no_holes(self):
        """Extract from polygon without holes returns empty list."""
        # Create simple polygon
        poly = Polygon([(0, 0), (10, 0), (10, 5), (0, 5)])

        # Extract hole vertices
        vertices = extract_hole_vertices(poly)

        # Should be empty
        assert len(vertices) == 0


class TestCriticalXCoordinates:
    """Test finding critical X-coordinates for vertical subdivision."""

    def test_block_with_hole_boundary(self):
        """Extract X-coords from non-convex block or Type B holes within block bounds."""
        # Create L-shaped block (non-convex, no hole)
        block_boundary = [
            (0, 0),
            (10, 0),
            (10, 5),
            (5, 5),
            (5, 10),
            (0, 10),
        ]
        block = Block(block_id=0, boundary=block_boundary)

        # Create inner boundary without holes
        inner_boundary = Polygon([(0, 0), (20, 0), (20, 20), (0, 20)])

        # Find critical X-coordinates (driving direction = 0° = East)
        critical_x = find_critical_x_coordinates(block, 0.0, inner_boundary)

        # Should include block boundaries and vertices from non-convex shape
        assert len(critical_x) >= 2, f"Expected at least 2 critical X coords, got {len(critical_x)}"
        assert 0.0 in critical_x or abs(min(critical_x) - 0.0) < 1e-5
        assert 10.0 in critical_x or abs(max(critical_x) - 10.0) < 1e-5

    def test_block_without_holes(self):
        """Block without holes returns only boundary X-coords."""
        # Create inner boundary without holes
        inner_boundary = Polygon([(0, 0), (20, 0), (20, 20), (0, 20)])

        # Create block
        block_boundary = [(0, 0), (20, 0), (20, 10), (0, 10)]
        block = Block(block_id=0, boundary=block_boundary)

        # Find critical X-coordinates
        critical_x = find_critical_x_coordinates(block, 0.0, inner_boundary)

        # Should return empty list (no holes to subdivide)
        assert len(critical_x) == 0


class TestVerticalSliceCreation:
    """Test creation of vertical slice polygons."""

    def test_create_vertical_slice(self):
        """Create vertical slice with correct area."""
        # Create slice from x=0 to x=5, y=0 to y=10
        slice_poly = create_vertical_slice(0.0, 5.0, 0.0, 10.0)

        # Check area
        assert abs(slice_poly.area - 50.0) < 1e-6

        # Check bounds
        bounds = slice_poly.bounds
        assert abs(bounds[0] - 0.0) < 1e-6  # minx
        assert abs(bounds[1] - 0.0) < 1e-6  # miny
        assert abs(bounds[2] - 5.0) < 1e-6  # maxx
        assert abs(bounds[3] - 10.0) < 1e-6  # maxy


class TestBlockSubdivision:
    """Test block subdivision logic."""

    def test_subdivide_convex_block(self):
        """Convex block should not be subdivided."""
        # Create rectangular block (convex)
        boundary = [(0, 0), (10, 0), (10, 5), (0, 5)]
        block = Block(block_id=0, boundary=boundary)

        # Create inner boundary without holes
        inner_boundary = Polygon([(0, 0), (20, 0), (20, 20), (0, 20)])

        # Subdivide (should return original block)
        result = subdivide_non_convex_block(block, 0.0, inner_boundary, next_block_id=1)

        # Should return 1 block (original)
        assert len(result) == 1
        assert result[0].block_id == 0

    def test_subdivide_vertical_slices(self):
        """Test vertical slicing of block."""
        # Create rectangular block
        boundary = [(0, 0), (10, 0), (10, 5), (0, 5)]
        block = Block(block_id=0, boundary=boundary)

        # Define critical X-coordinates (split block in half)
        critical_x = [0.0, 5.0, 10.0]

        # Subdivide vertically (rotation_angle = 0 for East driving direction)
        sub_polys = subdivide_block_vertically(block, critical_x, rotation_angle=0.0)

        # Should create 2 sub-blocks
        assert len(sub_polys) == 2

        # Check areas (each half should be 25.0)
        areas = [p.area for p in sub_polys]
        assert all(abs(a - 25.0) < 1e-6 for a in areas)


class TestBatchSubdivision:
    """Test batch subdivision of multiple blocks."""

    def test_subdivide_mixed_blocks(self):
        """Mix of convex and non-convex blocks."""
        # Create convex block
        convex_boundary = [(0, 0), (10, 0), (10, 5), (0, 5)]
        convex_block = Block(block_id=0, boundary=convex_boundary)

        # Create non-convex L-shaped block
        l_boundary = [(0, 10), (10, 10), (10, 15), (5, 15), (5, 20), (0, 20)]
        l_block = Block(block_id=1, boundary=l_boundary)

        # Create inner boundary with hole that affects L-block
        exterior = [(0, 0), (20, 0), (20, 30), (0, 30)]
        hole = [(4, 14), (6, 14), (6, 16), (4, 16)]
        inner_boundary = Polygon(exterior, [hole])

        # Batch subdivide
        blocks = [convex_block, l_block]
        result = subdivide_all_non_convex_blocks(blocks, 0.0, inner_boundary)

        # Should have at least original count (convex preserved, non-convex may split)
        assert len(result) >= len(blocks)

        # All blocks should have sequential IDs
        block_ids = [b.block_id for b in result]
        assert block_ids == list(range(len(result)))

    def test_subdivide_empty_list(self):
        """Empty block list returns empty."""
        inner_boundary = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])

        result = subdivide_all_non_convex_blocks([], 0.0, inner_boundary)

        assert len(result) == 0

    def test_area_preservation(self):
        """Total area should be preserved after subdivision."""
        # Create blocks
        block1 = Block(block_id=0, boundary=[(0, 0), (10, 0), (10, 5), (0, 5)])
        block2 = Block(block_id=1, boundary=[(0, 10), (10, 10), (10, 15), (0, 15)])

        # Calculate original total area
        original_area = sum(b.area for b in [block1, block2])

        # Create inner boundary
        inner_boundary = Polygon([(0, 0), (20, 0), (20, 30), (0, 30)])

        # Subdivide
        result = subdivide_all_non_convex_blocks([block1, block2], 0.0, inner_boundary)

        # Calculate new total area
        new_area = sum(b.area for b in result)

        # Area should be preserved (within tolerance)
        assert abs(new_area - original_area) < 1e-3


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_small_block(self):
        """Very small block should still be processed."""
        # Create tiny block
        boundary = [(0, 0), (0.1, 0), (0.1, 0.1), (0, 0.1)]
        block = Block(block_id=0, boundary=boundary)

        # Create inner boundary
        inner_boundary = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])

        # Subdivide
        result = subdivide_non_convex_block(block, 0.0, inner_boundary, next_block_id=1)

        # Should return at least original block
        assert len(result) >= 1

    def test_block_with_rotation(self):
        """Test subdivision with non-zero driving direction."""
        # Create rectangular block
        boundary = [(0, 0), (10, 0), (10, 5), (0, 5)]
        block = Block(block_id=0, boundary=boundary)

        # Create inner boundary without holes
        inner_boundary = Polygon([(-5, -5), (15, -5), (15, 10), (-5, 10)])

        # Subdivide with 45° driving direction
        result = subdivide_non_convex_block(block, 45.0, inner_boundary, next_block_id=1)

        # Should return original block (convex)
        assert len(result) == 1

    def test_nearly_zero_width_slice(self):
        """Test that zero-width slices are skipped."""
        # Create block
        boundary = [(0, 0), (10, 0), (10, 5), (0, 5)]
        block = Block(block_id=0, boundary=boundary)

        # Critical X with duplicate values (should create zero-width slice)
        critical_x = [0.0, 5.0, 5.0, 10.0]  # Duplicate 5.0

        # Subdivide
        sub_polys = subdivide_block_vertically(block, critical_x, rotation_angle=0.0)

        # Should skip zero-width slice, only create valid sub-blocks
        assert all(p.area > 1e-6 for p in sub_polys)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
