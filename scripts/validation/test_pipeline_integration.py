"""
Integration test for complete pipeline execution.

Tests the full ACO coverage path planning pipeline with the small scenario.
"""

import sys
from pathlib import Path

print("=" * 70)
print("PIPELINE INTEGRATION TEST")
print("=" * 70)

try:
    # Import components
    from src.dashboard import ConfigManager, ExportManager, run_complete_pipeline

    print("\n[Step 1] Loading small scenario configuration...")
    config_manager = ConfigManager()
    config = config_manager.load_scenario('small')
    print(f"  ✓ Loaded: {config.name}")
    print(f"  ✓ Field: {config.field_config['width']}x{config.field_config['height']}m")
    print(f"  ✓ Obstacles: {len(config.field_config['obstacles'])}")

    print("\n[Step 2] Running complete ACO pipeline...")
    print("  (This may take 30-60 seconds...)")
    results = run_complete_pipeline(config)

    if not results['success']:
        raise RuntimeError(f"Pipeline failed: {results.get('error', 'Unknown error')}")

    print("\n[Step 3] Validating results...")
    print(f"  ✓ Scenario: {results['scenario_name']}")
    print(f"  ✓ Field: {results['field_width']:.0f}x{results['field_height']:.0f}m")
    print(f"  ✓ Blocks: {results['num_blocks']}")
    print(f"  ✓ ACO Iterations: {results['num_iterations']}")
    print(f"  ✓ Initial Cost: {results['initial_cost']:.2f}")
    print(f"  ✓ Final Cost: {results['final_cost']:.2f}")
    print(f"  ✓ Improvement: {results['improvement_pct']:.2f}%")
    print(f"  ✓ Total Distance: {results['total_distance']:.2f}m")
    print(f"  ✓ Path Efficiency: {results['efficiency']:.2f}%")
    print(f"  ✓ Waypoints: {results['num_waypoints']}")

    print("\n[Step 4] Testing export functionality...")
    export_manager = ExportManager()

    # Test CSV export
    print("  Testing convergence CSV export...")
    conv_csv = export_manager.export_convergence_csv(
        results['solver'],
        filename="test_convergence.csv"
    )
    if not conv_csv.exists():
        raise FileNotFoundError(f"Convergence CSV not created: {conv_csv}")
    print(f"    ✓ Created: {conv_csv}")

    # Test statistics CSV export
    print("  Testing statistics CSV export...")
    stats_csv = export_manager.export_statistics_csv(
        results,
        filename="test_statistics.csv"
    )
    if not stats_csv.exists():
        raise FileNotFoundError(f"Statistics CSV not created: {stats_csv}")
    print(f"    ✓ Created: {stats_csv}")

    # Test static images export
    print("  Testing static images export...")
    image_paths = export_manager.export_static_images(
        field=results['field'],
        blocks=results['blocks'],
        path_plan=results['path_plan'],
        solver=results['solver'],
        prefix="test"
    )
    for img_type, img_path in image_paths.items():
        if not img_path.exists():
            raise FileNotFoundError(f"{img_type} image not created: {img_path}")
        print(f"    ✓ {img_type}: {img_path}")

    # Test PDF report generation
    print("  Testing PDF report generation...")
    pdf_path = export_manager.generate_pdf_report(
        results=results,
        image_paths=image_paths,
        animation_paths={},
        filename="test_report.pdf"
    )
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF report not created: {pdf_path}")
    print(f"    ✓ Created: {pdf_path} ({pdf_path.stat().st_size} bytes)")

    print("\n" + "=" * 70)
    print("INTEGRATION TEST: SUCCESS")
    print("=" * 70)
    print("✅ Complete pipeline executed successfully!")
    print("✅ All exports generated correctly!")
    print("\nGenerated test files:")
    print(f"  - {conv_csv}")
    print(f"  - {stats_csv}")
    print(f"  - {pdf_path}")
    for img_type, img_path in image_paths.items():
        print(f"  - {img_path}")
    print("\nReady to launch Streamlit dashboard!")
    print("=" * 70)

except Exception as e:
    print("\n" + "=" * 70)
    print("INTEGRATION TEST: FAILED")
    print("=" * 70)
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
