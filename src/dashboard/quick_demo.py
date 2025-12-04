"""
Quick Demo tab for Streamlit dashboard.

Provides one-click demos with pre-configured scenarios.
"""

import streamlit as st
from pathlib import Path
import time
from typing import Dict

from ..data import FieldParameters, create_field_with_rectangular_obstacles
from ..decomposition import boustrophedon_decomposition, merge_blocks_by_criteria
from ..geometry import generate_field_headland, generate_parallel_tracks
from ..obstacles.classifier import classify_all_obstacles, get_type_d_obstacles
from ..optimization import (
    ACOParameters, ACOSolver, build_cost_matrix,
    generate_path_from_solution
)
from ..visualization import PathAnimator, PheromoneAnimator

from .config_manager import ConfigManager, ScenarioConfig
from .export_utils import ExportManager


def run_complete_pipeline(config: ScenarioConfig) -> Dict:
    """
    Run complete ACO coverage path planning pipeline.

    Args:
        config: Scenario configuration

    Returns:
        Dictionary with all results
    """
    results = {
        'scenario_name': config.name,
        'success': False,
        'error': None
    }

    try:
        # Stage 1: Field Setup
        field = create_field_with_rectangular_obstacles(
            field_width=config.field_config['width'],
            field_height=config.field_config['height'],
            obstacle_specs=[
                (obs['x'], obs['y'], obs['width'], obs['height'])
                for obs in config.field_config['obstacles']
            ],
            name=config.name
        )

        params = FieldParameters(
            operating_width=config.parameters['operating_width'],
            turning_radius=config.parameters['turning_radius'],
            num_headland_passes=config.parameters['num_headland_passes'],
            driving_direction=config.parameters['driving_direction'],
            obstacle_threshold=config.parameters['obstacle_threshold']
        )

        # Store field info
        min_x, min_y, max_x, max_y = field.bounds
        results['field_width'] = max_x - min_x
        results['field_height'] = max_y - min_y
        results['num_obstacles'] = len(field.obstacles)
        results['operating_width'] = params.operating_width
        results['turning_radius'] = params.turning_radius
        results['driving_direction'] = params.driving_direction

        # Stage 2: Decomposition
        field_headland = generate_field_headland(
            field_boundary=field.boundary_polygon,
            operating_width=params.operating_width,
            num_passes=params.num_headland_passes,
        )

        classified_obstacles = classify_all_obstacles(
            obstacle_boundaries=field.obstacles,
            field_inner_boundary=field_headland.inner_boundary,
            driving_direction_degrees=params.driving_direction,
            operating_width=params.operating_width,
            threshold=params.obstacle_threshold,
        )

        type_d_obstacles = get_type_d_obstacles(classified_obstacles)
        obstacle_polygons = [obs.polygon for obs in type_d_obstacles]

        preliminary_blocks = boustrophedon_decomposition(
            inner_boundary=field_headland.inner_boundary,
            obstacles=obstacle_polygons,
            driving_direction_degrees=params.driving_direction,
        )

        final_blocks = merge_blocks_by_criteria(
            blocks=preliminary_blocks,
            operating_width=params.operating_width
        )

        results['num_blocks'] = len(final_blocks)

        # Generate tracks
        for block in final_blocks:
            tracks = generate_parallel_tracks(
                inner_boundary=block.polygon,
                driving_direction_degrees=params.driving_direction,
                operating_width=params.operating_width,
            )
            for i, track in enumerate(tracks):
                track.block_id = block.block_id
                track.index = i
            block.tracks = tracks

        # Stage 3: ACO Optimization
        all_nodes = []
        node_index = 0
        for block in final_blocks:
            nodes = block.create_entry_exit_nodes(start_index=node_index)
            all_nodes.extend(nodes)
            node_index += 4

        cost_matrix = build_cost_matrix(blocks=final_blocks, nodes=all_nodes)

        aco_params = ACOParameters(
            alpha=config.aco_params['alpha'],
            beta=config.aco_params['beta'],
            rho=config.aco_params['rho'],
            q=config.aco_params['q'],
            num_ants=config.aco_params['num_ants'],
            num_iterations=config.aco_params['num_iterations'],
            elitist_weight=config.aco_params['elitist_weight']
        )

        results['num_ants'] = aco_params.num_ants
        results['num_iterations'] = aco_params.num_iterations
        results['alpha'] = aco_params.alpha
        results['beta'] = aco_params.beta
        results['rho'] = aco_params.rho

        solver = ACOSolver(
            blocks=final_blocks,
            nodes=all_nodes,
            cost_matrix=cost_matrix,
            params=aco_params,
            record_history=config.aco_params.get('record_history', True),
            history_interval=config.aco_params.get('history_interval', 5)
        )

        best_solution = solver.solve(verbose=False)

        if not best_solution:
            results['error'] = "No valid solution found"
            return results

        # Get convergence data
        global_best, avg_costs = solver.get_convergence_data()
        results['initial_cost'] = global_best[0]
        results['final_cost'] = global_best[-1]
        results['improvement_pct'] = ((global_best[0] - global_best[-1]) / global_best[0]) * 100

        # Stage 4: Path Planning
        path_plan = generate_path_from_solution(
            solution=best_solution,
            blocks=final_blocks,
            nodes=all_nodes
        )

        results['total_distance'] = path_plan.total_distance
        results['working_distance'] = path_plan.working_distance
        results['transition_distance'] = path_plan.transition_distance
        results['efficiency'] = (path_plan.working_distance / path_plan.total_distance) * 100
        results['num_waypoints'] = len(path_plan.get_all_waypoints())

        # Store objects for visualization
        results['field'] = field
        results['blocks'] = final_blocks
        results['solver'] = solver
        results['path_plan'] = path_plan
        results['best_solution'] = best_solution
        results['visualization_config'] = config.visualization

        results['success'] = True

    except Exception as e:
        results['error'] = str(e)
        results['success'] = False

    return results


def render_quick_demo_tab():
    """Render the Quick Demo tab UI."""
    st.header("🚀 Quick Demo")
    st.markdown("Select a pre-configured scenario and run a complete demo with one click!")

    # Initialize managers
    if 'config_manager' not in st.session_state:
        st.session_state.config_manager = ConfigManager()

    if 'export_manager' not in st.session_state:
        st.session_state.export_manager = ExportManager()

    # Scenario selection
    st.subheader("Select Scenario")

    scenarios = {
        'small': {
            'name': 'Small Field Demo',
            'desc': '⚡ Quick demo with 3 obstacles - fast execution (~30 sec)',
            'icon': '🟢'
        },
        'medium': {
            'name': 'Medium Field Demo',
            'desc': '⚙️ Standard demo with 5 obstacles - typical complexity (~60 sec)',
            'icon': '🟡'
        },
        'large': {
            'name': 'Large Complex Field',
            'desc': '🎯 Complex demo with 7 obstacles - showcases algorithm power (~90 sec)',
            'icon': '🔴'
        }
    }

    selected_scenario = st.radio(
        "Choose a scenario:",
        options=list(scenarios.keys()),
        format_func=lambda x: f"{scenarios[x]['icon']} {scenarios[x]['name']} - {scenarios[x]['desc']}",
        key='scenario_selection'
    )

    st.markdown("---")

    # Run button
    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        run_button = st.button(
            "▶️ Run Demo",
            type="primary",
            use_container_width=True,
            key='run_demo_button'
        )

    # Run demo
    if run_button:
        with st.spinner(f"Running {scenarios[selected_scenario]['name']}..."):

            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Load configuration
            status_text.text("Loading configuration...")
            progress_bar.progress(10)
            time.sleep(0.2)

            try:
                config = st.session_state.config_manager.load_scenario(selected_scenario)
            except Exception as e:
                st.error(f"Failed to load scenario: {e}")
                return

            # Run pipeline
            status_text.text("Running ACO optimization...")
            progress_bar.progress(20)

            results = run_complete_pipeline(config)

            if not results['success']:
                st.error(f"Pipeline failed: {results['error']}")
                return

            progress_bar.progress(50)

            # Generate animations
            status_text.text("Generating path animation...")
            progress_bar.progress(60)

            timestamp = time.strftime("%Y%m%d_%H%M%S")

            # Path animation
            path_anim_file = st.session_state.export_manager.animations_dir / f"path_{timestamp}.gif"
            path_animator = PathAnimator(
                field=results['field'],
                blocks=results['blocks'],
                path_plan=results['path_plan'],
                fps=results['visualization_config'].get('animation_fps', 30),
                speed_multiplier=1.5
            )
            path_animator.save_animation(
                filename=str(path_anim_file),
                dpi=results['visualization_config'].get('animation_dpi', 100),
                writer='pillow'
            )

            progress_bar.progress(75)
            status_text.text("Generating pheromone animation...")

            # Pheromone animation
            pheromone_anim_file = st.session_state.export_manager.animations_dir / f"pheromone_{timestamp}.gif"
            pheromone_animator = PheromoneAnimator(
                solver=results['solver'],
                field=results['field'],
                blocks=results['blocks']
            )
            pheromone_animator.save_animation(
                filename=str(pheromone_anim_file),
                dpi=results['visualization_config'].get('animation_dpi', 100),
                fps=2
            )

            progress_bar.progress(85)
            status_text.text("Generating static images...")

            # Export static images
            image_paths = st.session_state.export_manager.export_static_images(
                field=results['field'],
                blocks=results['blocks'],
                path_plan=results['path_plan'],
                solver=results['solver'],
                prefix=f"demo_{timestamp}"
            )

            progress_bar.progress(90)
            status_text.text("Generating exports...")

            # Export CSV files
            conv_csv = st.session_state.export_manager.export_convergence_csv(
                results['solver'],
                filename=f"convergence_{timestamp}.csv"
            )

            stats_csv = st.session_state.export_manager.export_statistics_csv(
                results,
                filename=f"statistics_{timestamp}.csv"
            )

            # Generate PDF report
            pdf_path = st.session_state.export_manager.generate_pdf_report(
                results=results,
                image_paths=image_paths,
                animation_paths={
                    'path': path_anim_file,
                    'pheromone': pheromone_anim_file
                },
                filename=f"report_{timestamp}.pdf"
            )

            progress_bar.progress(100)
            status_text.text("✅ Complete!")
            time.sleep(0.5)

            # Store results in session state
            st.session_state.demo_results = {
                'results': results,
                'animations': {
                    'path': path_anim_file,
                    'pheromone': pheromone_anim_file
                },
                'images': image_paths,
                'exports': {
                    'convergence_csv': conv_csv,
                    'statistics_csv': stats_csv,
                    'pdf_report': pdf_path
                }
            }

            progress_bar.empty()
            status_text.empty()

    # Display results if available
    if 'demo_results' in st.session_state:
        st.markdown("---")
        st.subheader("📊 Results")

        results = st.session_state.demo_results['results']

        # Statistics in columns
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Best Cost",
                f"{results['final_cost']:.2f}",
                delta=f"-{results['improvement_pct']:.1f}%",
                delta_color="normal"
            )

        with col2:
            st.metric(
                "Path Efficiency",
                f"{results['efficiency']:.1f}%"
            )

        with col3:
            st.metric(
                "Total Distance",
                f"{results['total_distance']:.1f} m"
            )

        # Detailed statistics in expander
        with st.expander("📈 Detailed Statistics"):
            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("**Field Configuration**")
                st.text(f"Dimensions: {results['field_width']:.0f} × {results['field_height']:.0f} m")
                st.text(f"Obstacles: {results['num_obstacles']}")
                st.text(f"Blocks: {results['num_blocks']}")
                st.text(f"Operating Width: {results['operating_width']:.1f} m")

                st.markdown("**Path Statistics**")
                st.text(f"Waypoints: {results['num_waypoints']}")
                st.text(f"Working Distance: {results['working_distance']:.1f} m")
                st.text(f"Transition Distance: {results['transition_distance']:.1f} m")

            with col_b:
                st.markdown("**ACO Configuration**")
                st.text(f"Iterations: {results['num_iterations']}")
                st.text(f"Ants: {results['num_ants']}")
                st.text(f"Alpha: {results['alpha']:.1f}")
                st.text(f"Beta: {results['beta']:.1f}")
                st.text(f"Rho: {results['rho']:.1f}")

                st.markdown("**Optimization Results**")
                st.text(f"Initial Cost: {results['initial_cost']:.2f}")
                st.text(f"Final Cost: {results['final_cost']:.2f}")
                st.text(f"Improvement: {results['improvement_pct']:.1f}%")

        # Visualizations
        st.markdown("---")
        st.subheader("🎨 Visualizations")

        # Images in tabs
        tab1, tab2, tab3 = st.tabs(["Field Decomposition", "Coverage Path", "ACO Convergence"])

        with tab1:
            st.image(str(st.session_state.demo_results['images']['decomposition']))

        with tab2:
            st.image(str(st.session_state.demo_results['images']['path']))

        with tab3:
            st.image(str(st.session_state.demo_results['images']['convergence']))

        # Download section
        st.markdown("---")
        st.subheader("📥 Download Results")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Animations**")

            # Path animation
            with open(st.session_state.demo_results['animations']['path'], 'rb') as f:
                st.download_button(
                    label="⬇️ Path Animation (GIF)",
                    data=f,
                    file_name=st.session_state.demo_results['animations']['path'].name,
                    mime="image/gif"
                )

            # Pheromone animation
            with open(st.session_state.demo_results['animations']['pheromone'], 'rb') as f:
                st.download_button(
                    label="⬇️ Pheromone Animation (GIF)",
                    data=f,
                    file_name=st.session_state.demo_results['animations']['pheromone'].name,
                    mime="image/gif"
                )

        with col2:
            st.markdown("**Data & Reports**")

            # PDF Report
            with open(st.session_state.demo_results['exports']['pdf_report'], 'rb') as f:
                st.download_button(
                    label="📄 PDF Report",
                    data=f,
                    file_name=st.session_state.demo_results['exports']['pdf_report'].name,
                    mime="application/pdf"
                )

            # Convergence CSV
            with open(st.session_state.demo_results['exports']['convergence_csv'], 'rb') as f:
                st.download_button(
                    label="📊 Convergence Data (CSV)",
                    data=f,
                    file_name=st.session_state.demo_results['exports']['convergence_csv'].name,
                    mime="text/csv"
                )

            # Statistics CSV
            with open(st.session_state.demo_results['exports']['statistics_csv'], 'rb') as f:
                st.download_button(
                    label="📊 Statistics (CSV)",
                    data=f,
                    file_name=st.session_state.demo_results['exports']['statistics_csv'].name,
                    mime="text/csv"
                )
