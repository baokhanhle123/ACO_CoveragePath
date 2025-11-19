"""
Block data structure representing a sub-field after decomposition.
"""
from typing import List, Tuple, Optional
from dataclasses import dataclass, field
from shapely.geometry import Polygon
import numpy as np

from .track import Track


@dataclass
class BlockNode:
    """
    Entry/exit node for a block.

    According to the paper, each block has 4 nodes:
    - n_i1, n_i2: endpoints of first track
    - n_i3, n_i4: endpoints of last track
    """

    position: Tuple[float, float]  # (x, y) coordinate
    block_id: int  # Block this node belongs to
    node_type: str  # "first_start", "first_end", "last_start", "last_end"
    index: int  # Node global index in TSP graph

    def __repr__(self) -> str:
        return f"Node(n_{self.block_id}{self.index % 4 + 1}, {self.position})"


@dataclass
class Block:
    """
    Represents a sub-field block after decomposition.

    A block is an obstacle-free region containing parallel tracks.

    Attributes:
        block_id: Unique block identifier
        boundary: List of (x, y) coordinates defining block boundary
        tracks: List of Track objects in this block
        nodes: Entry/exit nodes (4 nodes: first track endpoints + last track endpoints)
    """

    block_id: int
    boundary: List[Tuple[float, float]]
    tracks: List[Track] = field(default_factory=list)
    nodes: List[BlockNode] = field(default_factory=list)

    _polygon: Optional[Polygon] = field(default=None, init=False, repr=False)

    @property
    def polygon(self) -> Polygon:
        """Get Shapely Polygon representation."""
        if self._polygon is None:
            self._polygon = Polygon(self.boundary)
        return self._polygon

    @property
    def area(self) -> float:
        """Calculate block area."""
        return self.polygon.area

    @property
    def num_tracks(self) -> int:
        """Get number of tracks in block."""
        return len(self.tracks)

    @property
    def is_odd_tracks(self) -> bool:
        """Check if block has odd number of tracks (affects entry/exit logic)."""
        return self.num_tracks % 2 == 1

    @property
    def parity_function(self) -> int:
        """
        Parity function e_i = (-1)^(mod(|T_i|, 2))
        Returns 1 for odd number of tracks, -1 for even.
        """
        return 1 if self.is_odd_tracks else -1

    def get_first_track(self) -> Optional[Track]:
        """Get first track in block."""
        return self.tracks[0] if self.tracks else None

    def get_last_track(self) -> Optional[Track]:
        """Get last track in block."""
        return self.tracks[-1] if self.tracks else None

    def get_working_distance(self) -> float:
        """Calculate total working distance (sum of track lengths)."""
        return sum(track.length for track in self.tracks)

    def create_entry_exit_nodes(self, start_index: int) -> List[BlockNode]:
        """
        Create 4 entry/exit nodes for this block.

        Args:
            start_index: Starting index for node numbering in global graph

        Returns:
            List of 4 BlockNode objects
        """
        if not self.tracks:
            raise ValueError(f"Block {self.block_id} has no tracks")

        first_track = self.get_first_track()
        last_track = self.get_last_track()

        self.nodes = [
            BlockNode(first_track.start, self.block_id, "first_start", start_index),
            BlockNode(first_track.end, self.block_id, "first_end", start_index + 1),
            BlockNode(last_track.start, self.block_id, "last_start", start_index + 2),
            BlockNode(last_track.end, self.block_id, "last_end", start_index + 3),
        ]

        return self.nodes

    def get_node_by_type(self, node_type: str) -> Optional[BlockNode]:
        """Get node by type (first_start, first_end, last_start, last_end)."""
        for node in self.nodes:
            if node.node_type == node_type:
                return node
        return None

    def __repr__(self) -> str:
        return (f"Block({self.block_id}, tracks={self.num_tracks}, "
                f"area={self.area:.2f}m², parity={self.parity_function})")


@dataclass
class BlockGraph:
    """
    Adjacency graph for blocks (used in merging preliminary blocks).

    Attributes:
        blocks: List of Block objects
        adjacency: Dictionary mapping block_id to list of adjacent block_ids
    """

    blocks: List[Block] = field(default_factory=list)
    adjacency: dict = field(default_factory=dict)

    def add_block(self, block: Block):
        """Add a block to the graph."""
        self.blocks.append(block)
        if block.block_id not in self.adjacency:
            self.adjacency[block.block_id] = []

    def add_edge(self, block_id_1: int, block_id_2: int):
        """Add adjacency edge between two blocks."""
        if block_id_1 not in self.adjacency:
            self.adjacency[block_id_1] = []
        if block_id_2 not in self.adjacency:
            self.adjacency[block_id_2] = []

        if block_id_2 not in self.adjacency[block_id_1]:
            self.adjacency[block_id_1].append(block_id_2)
        if block_id_1 not in self.adjacency[block_id_2]:
            self.adjacency[block_id_2].append(block_id_1)

    def get_adjacent_blocks(self, block_id: int) -> List[int]:
        """Get list of adjacent block IDs."""
        return self.adjacency.get(block_id, [])

    def get_block_by_id(self, block_id: int) -> Optional[Block]:
        """Get block by ID."""
        for block in self.blocks:
            if block.block_id == block_id:
                return block
        return None

    def __repr__(self) -> str:
        return f"BlockGraph(blocks={len(self.blocks)}, edges={sum(len(adj) for adj in self.adjacency.values()) // 2})"
