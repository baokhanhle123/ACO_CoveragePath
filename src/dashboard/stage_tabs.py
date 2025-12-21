"""
Stage-specific tab rendering for Streamlit dashboard.

Provides dedicated tabs for viewing each stage of the 3-stage pipeline
with detailed visualizations and statistics.
"""

import streamlit as st

from ..visualization.stage_viz import (
    plot_stage1_result,
    plot_stage2_result,
    plot_stage3_result
)


def render_stage1_tab():
    """Render Stage 1 dedicated tab with detailed visualization."""
    st.header("📐 Stage 1: Field Geometric Representation")

    st.markdown("""
    **Stage 1** handles field geometry, obstacle classification, and global track generation.

    Key steps:
    1. Generate field headlands (buffer zones)
    2. Classify obstacles into Types A, B, C, D
    3. Regenerate headland with Type B obstacles incorporated
    4. Generate parallel tracks covering the field body
    """)

    if 'demo_results' not in st.session_state:
        st.info("⚠️ **No data available.** Run a demo from the Quick Demo tab first to see Stage 1 results.")
        return

    results = st.session_state.demo_results['results']

    if 'stage1_result' not in results:
        st.warning("Stage 1 results not available. Please run the demo again.")
        return

    # Display Stage 1 summary statistics
    st.subheader("Stage 1 Summary")
    col1, col2, col3, col4 = st.columns(4)

    stage1 = results['stage1_result']

    with col1:
        st.metric("Total Obstacles", len(stage1.classified_obstacles))

    with col2:
        type_b_count = len(stage1.type_b_obstacles)
        st.metric("Type B (Boundary)", type_b_count)
        if type_b_count > 0:
            st.caption("Incorporated into headland")

    with col3:
        type_d_count = len(stage1.type_d_obstacles)
        st.metric("Type D (Decompose)", type_d_count)
        if type_d_count > 0:
            st.caption("Require decomposition")

    with col4:
        st.metric("Global Tracks", results['num_global_tracks'])
        total_length = sum(t.length for t in stage1.tracks)
        st.caption(f"Total: {total_length:.1f}m")

    # Generate and display visualization
    st.subheader("Stage 1 Visualization")
    try:
        fig = plot_stage1_result(stage1)
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Error generating visualization: {e}")

    # Detailed breakdowns in expanders
    with st.expander("📊 Obstacle Classification Details"):
        if stage1.classified_obstacles:
            for obs in stage1.classified_obstacles:
                obs_type = obs.obstacle_type.name
                area = obs.polygon.area
                st.text(f"Obstacle {obs.original_index}: Type {obs_type} - Area: {area:.1f} m²")

                if obs.is_merged():
                    merged_from = sorted(list(obs.merged_from))
                    st.caption(f"  → Merged from obstacles: {merged_from}")
        else:
            st.info("No obstacles classified.")

    with st.expander("📏 Track Statistics"):
        if stage1.tracks:
            total_length = sum(t.length for t in stage1.tracks)
            avg_length = total_length / len(stage1.tracks)
            min_length = min(t.length for t in stage1.tracks)
            max_length = max(t.length for t in stage1.tracks)

            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                st.metric("Total Tracks", len(stage1.tracks))
            with col_b:
                st.metric("Total Length", f"{total_length:.1f}m")
            with col_c:
                st.metric("Avg Length", f"{avg_length:.1f}m")
            with col_d:
                st.metric("Range", f"{min_length:.1f}-{max_length:.1f}m")

            st.caption("These global tracks will be clustered into blocks in Stage 2.")
        else:
            st.info("No tracks generated.")


def render_stage2_tab():
    """Render Stage 2 dedicated tab with decomposition visualization."""
    st.header("🔲 Stage 2: Boustrophedon Decomposition")

    st.markdown("""
    **Stage 2** decomposes the field into blocks and clusters tracks.

    Key steps:
    1. Boustrophedon decomposition (create cells perpendicular to driving direction)
    2. Merge adjacent blocks to reduce count
    3. **Cluster global tracks from Stage 1 into blocks** (Zhou et al. 2014 Section 2.3.2)
    """)

    if 'demo_results' not in st.session_state:
        st.info("⚠️ **No data available.** Run a demo from the Quick Demo tab first to see Stage 2 results.")
        return

    results = st.session_state.demo_results['results']

    if 'stage1_result' not in results:
        st.warning("Stage 1 results required. Please run the demo again.")
        return

    # Display Stage 2 summary statistics
    st.subheader("Stage 2 Summary")
    col1, col2, col3 = st.columns(3)

    preliminary_blocks = results.get('preliminary_blocks', [])
    final_blocks = results['blocks']

    with col1:
        st.metric("Preliminary Blocks", len(preliminary_blocks))
        st.caption("Before merging")

    with col2:
        reduction = len(preliminary_blocks) - len(final_blocks) if preliminary_blocks else 0
        filtered = results.get('num_blocks_filtered', 0)
        st.metric("Final Blocks", len(final_blocks))
        if reduction > 0:
            st.caption(f"Reduced by {reduction} (merging)")
        if filtered > 0:
            st.caption(f"⚠️ Filtered {filtered} (no tracks)")

    with col3:
        total_track_segments = sum(len(b.tracks) for b in final_blocks)
        st.metric("Track Segments", total_track_segments)
        st.caption(f"Clustered from {results['num_global_tracks']} global tracks")

    # Generate and display visualization
    st.subheader("Stage 2 Visualization")
    try:
        fig = plot_stage2_result(
            results['stage1_result'],
            preliminary_blocks,
            final_blocks
        )
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Error generating visualization: {e}")

    # Block details
    with st.expander("📦 Block Details"):
        if final_blocks:
            st.markdown("**Final Blocks After Merging:**")
            for block in final_blocks:
                area = block.polygon.area
                num_tracks = len(block.tracks)
                working_distance = block.get_working_distance()
                parity = "Odd" if block.is_odd_tracks else "Even"

                st.text(
                    f"Block {block.block_id}: "
                    f"Area={area:.1f}m², "
                    f"Tracks={num_tracks} ({parity}), "
                    f"Working distance={working_distance:.1f}m"
                )
        else:
            st.info("No blocks available.")

    with st.expander("🔄 Track Clustering Algorithm"):
        st.markdown("""
        **Track Clustering Process (Zhou et al. 2014, Section 2.3.2):**

        1. **Input**: Global tracks from Stage 1 (generated ignoring obstacles)
        2. **For each track**:
           - Check intersection with each block boundary
           - If intersects, subdivide track at intersection points
           - Assign track segments to their respective blocks
        3. **Result**: Each block has its own set of track segments

        **Why clustering instead of per-block generation?**
        - ✅ Ensures consistent track spacing across the entire field
        - ✅ Matches the algorithm specification in the research paper
        - ✅ Preserves total track length (segments sum to global tracks)
        """)


def render_stage3_tab():
    """Render Stage 3 dedicated tab with ACO optimization visualization."""
    st.header("🎯 Stage 3: ACO Path Optimization")

    st.markdown("""
    **Stage 3** uses Ant Colony Optimization to find the optimal block visit sequence.

    Key steps:
    1. Create 4 entry/exit nodes per block (first_start, first_end, last_start, last_end)
    2. Build cost matrix (working distance within blocks, transition distance between blocks)
    3. Run ACO optimization with pheromone trails and heuristic guidance
    4. Generate continuous coverage path from optimal solution
    """)

    if 'demo_results' not in st.session_state:
        st.info("⚠️ **No data available.** Run a demo from the Quick Demo tab first to see Stage 3 results.")
        return

    results = st.session_state.demo_results['results']

    # Show warning if blocks were filtered
    if 'blocks_filtered_warning' in results:
        st.warning(f"ℹ️ {results['blocks_filtered_warning']}")

    # Display Stage 3 summary statistics
    st.subheader("Stage 3 Summary")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        efficiency = results['efficiency']
        st.metric(
            "Path Efficiency",
            f"{efficiency:.1f}%"
        )
        if efficiency >= 90:
            st.caption("✅ Excellent")
        elif efficiency >= 85:
            st.caption("✅ Good")
        else:
            st.caption("⚠️ Below target")

    with col2:
        improvement_pct = results['improvement_pct']
        st.metric(
            "ACO Improvement",
            f"{improvement_pct:.1f}%",
            delta=f"-{improvement_pct:.1f}%"
        )
        if improvement_pct >= 20:
            st.caption("✅ Significant")
        elif improvement_pct >= 10:
            st.caption("✅ Good")
        else:
            st.caption("⚠️ Minor")

    with col3:
        total_dist = results['total_distance']
        st.metric(
            "Total Distance",
            f"{total_dist:.1f}m"
        )
        st.caption(f"Working: {results['working_distance']:.1f}m")

    with col4:
        transition_dist = results['transition_distance']
        st.metric(
            "Transition Distance",
            f"{transition_dist:.1f}m"
        )
        transition_pct = (transition_dist / total_dist) * 100 if total_dist > 0 else 0
        st.caption(f"{transition_pct:.1f}% of total")

    # Generate and display visualizations
    st.subheader("Stage 3 Visualization")
    try:
        path_fig, conv_fig = plot_stage3_result(
            results['field'],
            results['blocks'],
            results['path_plan'],
            results['solver']
        )

        col1, col2 = st.columns(2)
        with col1:
            st.pyplot(path_fig)
        with col2:
            st.pyplot(conv_fig)
    except Exception as e:
        st.error(f"Error generating visualization: {e}")

    # ACO parameters and results
    with st.expander("🐜 ACO Algorithm Details"):
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("**Algorithm Parameters:**")
            st.text(f"Iterations: {results['num_iterations']}")
            st.text(f"Ants per iteration: {results['num_ants']}")
            st.text(f"Alpha (pheromone weight): {results['alpha']:.1f}")
            st.text(f"Beta (heuristic weight): {results['beta']:.1f}")
            st.text(f"Rho (evaporation rate): {results['rho']:.2f}")

        with col_b:
            st.markdown("**Optimization Results:**")
            st.text(f"Initial cost: {results['initial_cost']:.2f}m")
            st.text(f"Final cost: {results['final_cost']:.2f}m")
            st.text(f"Improvement: {results['improvement_pct']:.1f}%")
            st.text(f"Blocks visited: {results['num_blocks']}")

    with st.expander("📊 Path Composition"):
        path_plan = results['path_plan']
        num_segments = len(path_plan.segments)
        num_working = sum(1 for seg in path_plan.segments if seg.segment_type == "working")
        num_transition = num_segments - num_working

        col_a, col_b, col_c = st.columns(3)

        with col_a:
            st.metric("Total Segments", num_segments)

        with col_b:
            st.metric("Working Segments", num_working)
            st.caption(f"{results['working_distance']:.1f}m")

        with col_c:
            st.metric("Transition Segments", num_transition)
            st.caption(f"{results['transition_distance']:.1f}m")

        # Block visit order
        st.markdown("**Block Visit Order:**")
        block_sequence = path_plan.block_sequence
        # Remove duplicates (each block visited twice for entry/exit)
        unique_blocks = []
        for block_id in block_sequence:
            if not unique_blocks or unique_blocks[-1] != block_id:
                unique_blocks.append(block_id)

        sequence_str = " → ".join(f"B{block_id}" for block_id in unique_blocks)
        st.text(sequence_str)
