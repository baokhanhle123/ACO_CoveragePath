"""
Export utilities for dashboard.

Handles PDF report generation, CSV data export, PNG image export,
and GIF animation management.
"""

import io
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import numpy as np


class PDFReport(FPDF):
    """Custom PDF report class."""

    def header(self):
        """Page header."""
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'ACO Coverage Path Planning - Analysis Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        """Page footer."""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title: str):
        """Add chapter title."""
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(4)

    def add_text(self, text: str):
        """Add body text."""
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def add_table_row(self, label: str, value: str, bold_label: bool = True):
        """Add key-value table row."""
        if bold_label:
            self.set_font('Arial', 'B', 11)
        else:
            self.set_font('Arial', '', 11)
        self.cell(80, 6, label, 0, 0, 'L')
        self.set_font('Arial', '', 11)
        self.cell(0, 6, str(value), 0, 1, 'L')


class ExportManager:
    """Manages all export operations."""

    def __init__(self, export_base_dir: str = "exports"):
        """
        Initialize export manager.

        Args:
            export_base_dir: Base directory for exports
        """
        self.base_dir = Path(export_base_dir)
        self.animations_dir = self.base_dir / "animations"
        self.reports_dir = self.base_dir / "reports"
        self.data_dir = self.base_dir / "data"
        self.images_dir = self.base_dir / "images"

        # Create directories
        for directory in [self.animations_dir, self.reports_dir,
                         self.data_dir, self.images_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def export_convergence_csv(
        self,
        solver,
        filename: Optional[str] = None
    ) -> Path:
        """
        Export convergence data to CSV.

        Args:
            solver: ACOSolver instance with results
            filename: Optional custom filename

        Returns:
            Path to saved CSV file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"convergence_{timestamp}.csv"

        # Get convergence data
        global_best, avg_costs = solver.get_convergence_data()

        # Create DataFrame
        df = pd.DataFrame({
            'iteration': list(range(len(global_best))),
            'best_cost': global_best,
            'average_cost': avg_costs
        })

        # Save
        output_path = self.data_dir / filename
        df.to_csv(output_path, index=False)

        return output_path

    def export_statistics_csv(
        self,
        results: Dict,
        filename: Optional[str] = None
    ) -> Path:
        """
        Export comprehensive statistics to CSV.

        Args:
            results: Results dictionary with all metrics
            filename: Optional custom filename

        Returns:
            Path to saved CSV file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"statistics_{timestamp}.csv"

        # Extract statistics
        stats = []

        # Field configuration
        stats.append(["Field Configuration", ""])
        stats.append(["Field Width (m)", results.get('field_width', 'N/A')])
        stats.append(["Field Height (m)", results.get('field_height', 'N/A')])
        stats.append(["Number of Obstacles", results.get('num_obstacles', 'N/A')])
        stats.append(["Number of Blocks", results.get('num_blocks', 'N/A')])
        stats.append(["", ""])

        # Planning parameters
        stats.append(["Planning Parameters", ""])
        stats.append(["Operating Width (m)", results.get('operating_width', 'N/A')])
        stats.append(["Turning Radius (m)", results.get('turning_radius', 'N/A')])
        stats.append(["Driving Direction (deg)", results.get('driving_direction', 'N/A')])
        stats.append(["", ""])

        # ACO Results
        stats.append(["ACO Results", ""])
        stats.append(["Initial Cost", f"{results.get('initial_cost', 0):.2f}"])
        stats.append(["Final Cost", f"{results.get('final_cost', 0):.2f}"])
        stats.append(["Cost Improvement (%)", f"{results.get('improvement_pct', 0):.2f}"])
        stats.append(["Number of Iterations", results.get('num_iterations', 'N/A')])
        stats.append(["Number of Ants", results.get('num_ants', 'N/A')])
        stats.append(["", ""])

        # Path Statistics
        stats.append(["Path Statistics", ""])
        stats.append(["Total Distance (m)", f"{results.get('total_distance', 0):.2f}"])
        stats.append(["Working Distance (m)", f"{results.get('working_distance', 0):.2f}"])
        stats.append(["Transition Distance (m)", f"{results.get('transition_distance', 0):.2f}"])
        stats.append(["Path Efficiency (%)", f"{results.get('efficiency', 0):.2f}"])
        stats.append(["Number of Waypoints", results.get('num_waypoints', 'N/A')])

        # Create DataFrame
        df = pd.DataFrame(stats, columns=['Metric', 'Value'])

        # Save
        output_path = self.data_dir / filename
        df.to_csv(output_path, index=False)

        return output_path

    def export_static_images(
        self,
        field,
        blocks,
        path_plan,
        solver,
        prefix: Optional[str] = None
    ) -> Dict[str, Path]:
        """
        Export static PNG images.

        Args:
            field: Field object
            blocks: List of blocks
            path_plan: PathPlan object
            solver: ACOSolver instance
            prefix: Optional filename prefix

        Returns:
            Dictionary mapping image type to file path
        """
        if prefix is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prefix = f"image_{timestamp}"

        images = {}

        # 1. Field Decomposition
        fig, ax = plt.subplots(figsize=(12, 10))

        # Draw field boundary
        field_x, field_y = zip(*field.boundary_polygon.exterior.coords)
        ax.plot(field_x, field_y, 'k-', linewidth=2, label='Field Boundary')

        # Draw obstacles
        for obs in field.obstacle_polygons:
            obs_x, obs_y = zip(*obs.exterior.coords)
            ax.fill(obs_x, obs_y, color='gray', alpha=0.5, edgecolor='black')

        # Draw blocks
        import matplotlib.cm as cm
        colors = cm.Set3(np.linspace(0, 1, len(blocks)))
        for i, block in enumerate(blocks):
            block_x, block_y = zip(*block.polygon.exterior.coords)
            ax.fill(block_x, block_y, color=colors[i], alpha=0.3,
                   edgecolor=colors[i], linewidth=2)
            # Add block label
            centroid = block.polygon.centroid
            ax.text(centroid.x, centroid.y, f"B{i}",
                   fontsize=12, ha='center', fontweight='bold')

        ax.set_xlabel('X (meters)', fontsize=12)
        ax.set_ylabel('Y (meters)', fontsize=12)
        ax.set_title('Field Decomposition', fontsize=14, fontweight='bold')
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)

        decomp_path = self.images_dir / f"{prefix}_decomposition.png"
        plt.savefig(decomp_path, dpi=150, bbox_inches='tight')
        plt.close()
        images['decomposition'] = decomp_path

        # 2. Coverage Path
        fig, ax = plt.subplots(figsize=(12, 10))

        # Redraw field and blocks (lighter)
        ax.plot(field_x, field_y, 'k-', linewidth=1, alpha=0.5)
        for obs in field.obstacle_polygons:
            obs_x, obs_y = zip(*obs.exterior.coords)
            ax.fill(obs_x, obs_y, color='gray', alpha=0.3)
        for i, block in enumerate(blocks):
            block_x, block_y = zip(*block.polygon.exterior.coords)
            ax.fill(block_x, block_y, color=colors[i], alpha=0.15)

        # Draw path
        waypoints = path_plan.get_all_waypoints()
        path_x = [p[0] for p in waypoints]
        path_y = [p[1] for p in waypoints]
        ax.plot(path_x, path_y, 'b-', linewidth=2, label='Coverage Path')
        ax.plot(path_x[0], path_y[0], 'go', markersize=10, label='Start')
        ax.plot(path_x[-1], path_y[-1], 'ro', markersize=10, label='End')

        ax.set_xlabel('X (meters)', fontsize=12)
        ax.set_ylabel('Y (meters)', fontsize=12)
        ax.set_title('Coverage Path', fontsize=14, fontweight='bold')
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.legend()

        path_path = self.images_dir / f"{prefix}_path.png"
        plt.savefig(path_path, dpi=150, bbox_inches='tight')
        plt.close()
        images['path'] = path_path

        # 3. Convergence Plot
        fig, ax = plt.subplots(figsize=(10, 6))

        global_best, avg_costs = solver.get_convergence_data()
        iterations = list(range(len(global_best)))

        ax.plot(iterations, global_best, 'g-', linewidth=2, label='Best Cost')
        ax.plot(iterations, avg_costs, 'b--', linewidth=1.5, alpha=0.6, label='Avg Cost')

        ax.set_xlabel('Iteration', fontsize=12)
        ax.set_ylabel('Cost', fontsize=12)
        ax.set_title('ACO Convergence', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()

        conv_path = self.images_dir / f"{prefix}_convergence.png"
        plt.savefig(conv_path, dpi=150, bbox_inches='tight')
        plt.close()
        images['convergence'] = conv_path

        return images

    def generate_pdf_report(
        self,
        results: Dict,
        image_paths: Dict[str, Path],
        animation_paths: Dict[str, Path],
        filename: Optional[str] = None
    ) -> Path:
        """
        Generate comprehensive PDF report.

        Args:
            results: Results dictionary with all metrics
            image_paths: Paths to static images
            animation_paths: Paths to animations (for reference)
            filename: Optional custom filename

        Returns:
            Path to saved PDF file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.pdf"

        pdf = PDFReport()
        pdf.add_page()

        # Title page info
        pdf.chapter_title("Analysis Summary")
        pdf.add_text(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        pdf.add_text(f"Scenario: {results.get('scenario_name', 'Custom Configuration')}")
        pdf.ln(5)

        # Field Configuration
        pdf.chapter_title("1. Field Configuration")
        pdf.add_table_row("Field Dimensions:", f"{results.get('field_width', 0):.0f} m × {results.get('field_height', 0):.0f} m")
        pdf.add_table_row("Number of Obstacles:", str(results.get('num_obstacles', 'N/A')))
        pdf.add_table_row("Number of Blocks:", str(results.get('num_blocks', 'N/A')))
        pdf.add_table_row("Operating Width:", f"{results.get('operating_width', 0):.1f} m")
        pdf.add_table_row("Turning Radius:", f"{results.get('turning_radius', 0):.1f} m")
        pdf.ln(5)

        # ACO Configuration
        pdf.chapter_title("2. ACO Configuration")
        pdf.add_table_row("Number of Ants:", str(results.get('num_ants', 'N/A')))
        pdf.add_table_row("Number of Iterations:", str(results.get('num_iterations', 'N/A')))
        pdf.add_table_row("Alpha (Pheromone Weight):", f"{results.get('alpha', 0):.2f}")
        pdf.add_table_row("Beta (Heuristic Weight):", f"{results.get('beta', 0):.2f}")
        pdf.add_table_row("Rho (Evaporation Rate):", f"{results.get('rho', 0):.2f}")
        pdf.ln(5)

        # Optimization Results
        pdf.chapter_title("3. Optimization Results")
        pdf.add_table_row("Initial Cost:", f"{results.get('initial_cost', 0):.2f}")
        pdf.add_table_row("Final Cost:", f"{results.get('final_cost', 0):.2f}")
        pdf.add_table_row("Cost Improvement:", f"{results.get('improvement_pct', 0):.2f}%")
        pdf.ln(5)

        # Path Statistics
        pdf.chapter_title("4. Path Statistics")
        pdf.add_table_row("Total Distance:", f"{results.get('total_distance', 0):.2f} m")
        pdf.add_table_row("Working Distance:", f"{results.get('working_distance', 0):.2f} m")
        pdf.add_table_row("Transition Distance:", f"{results.get('transition_distance', 0):.2f} m")
        pdf.add_table_row("Path Efficiency:", f"{results.get('efficiency', 0):.2f}%")
        pdf.add_table_row("Number of Waypoints:", str(results.get('num_waypoints', 'N/A')))

        # Add images
        if 'decomposition' in image_paths:
            pdf.add_page()
            pdf.chapter_title("5. Field Decomposition")
            pdf.image(str(image_paths['decomposition']), x=10, w=190)

        if 'path' in image_paths:
            pdf.add_page()
            pdf.chapter_title("6. Coverage Path")
            pdf.image(str(image_paths['path']), x=10, w=190)

        if 'convergence' in image_paths:
            pdf.add_page()
            pdf.chapter_title("7. ACO Convergence")
            pdf.image(str(image_paths['convergence']), x=10, w=190)

        # Animation references
        pdf.add_page()
        pdf.chapter_title("8. Animation Files")
        pdf.add_text("The following animation files have been generated:")
        pdf.ln(2)

        for anim_type, anim_path in animation_paths.items():
            pdf.add_table_row(f"{anim_type.title()} Animation:", anim_path.name, bold_label=False)

        # Save PDF
        output_path = self.reports_dir / filename
        pdf.output(str(output_path))

        return output_path
