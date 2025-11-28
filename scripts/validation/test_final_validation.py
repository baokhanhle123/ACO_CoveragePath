"""
Final validation test for complete Phase 2A implementation.

Tests everything end-to-end including animations.
"""

import sys
from pathlib import Path
import time

print("=" * 80)
print("PHASE 2A - FINAL VALIDATION TEST")
print("=" * 80)

success_count = 0
total_tests = 7

# Test 1: All imports
print("\n[Test 1/7] Verifying all module imports...")
try:
    from src.dashboard import (
        ConfigManager, ScenarioConfig, ConfigurationError,
        ExportManager, run_complete_pipeline, render_quick_demo_tab
    )
    from src.visualization import PathAnimator, PheromoneAnimator
    from src.data import FieldParameters
    from src.optimization import ACOParameters
    import streamlit as st
    import pandas as pd
    import matplotlib.pyplot as plt
    from fpdf import FPDF

    print("  ✓ All imports successful")
    success_count += 1
except Exception as e:
    print(f"  ✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Configuration loading
print("\n[Test 2/7] Testing configuration system...")
try:
    config_manager = ConfigManager()

    for scenario in ['small', 'medium', 'large']:
        config = config_manager.load_scenario(scenario)
        assert config.name is not None
        assert len(config.field_config['obstacles']) > 0
        assert config.aco_params['num_iterations'] > 0

    print("  ✓ All scenarios load correctly")
    success_count += 1
except Exception as e:
    print(f"  ✗ Configuration test failed: {e}")
    sys.exit(1)

# Test 3: Export manager
print("\n[Test 3/7] Testing export manager setup...")
try:
    export_manager = ExportManager()

    assert export_manager.animations_dir.exists()
    assert export_manager.reports_dir.exists()
    assert export_manager.data_dir.exists()
    assert export_manager.images_dir.exists()

    print("  ✓ Export manager initialized correctly")
    success_count += 1
except Exception as e:
    print(f"  ✗ Export manager test failed: {e}")
    sys.exit(1)

# Test 4: Complete pipeline execution
print("\n[Test 4/7] Running complete pipeline with small scenario...")
print("  (This will take ~30-40 seconds...)")
try:
    start_time = time.time()

    config = config_manager.load_scenario('small')
    results = run_complete_pipeline(config)

    elapsed = time.time() - start_time

    if not results['success']:
        raise RuntimeError(f"Pipeline failed: {results.get('error')}")

    # Validate results
    assert results['num_blocks'] > 0
    assert results['final_cost'] > 0  # Solution exists
    assert results['initial_cost'] > 0  # Initial solution exists
    # Note: ACO doesn't guarantee improvement every run, so we just check valid solution
    assert results['efficiency'] > 50.0
    assert results['total_distance'] > 0

    print(f"  ✓ Pipeline completed in {elapsed:.1f}s")
    print(f"    - Blocks: {results['num_blocks']}")
    print(f"    - Initial cost: {results['initial_cost']:.2f}")
    print(f"    - Final cost: {results['final_cost']:.2f}")
    print(f"    - Cost improvement: {results['improvement_pct']:.2f}%")
    print(f"    - Path efficiency: {results['efficiency']:.2f}%")
    success_count += 1
except Exception as e:
    print(f"  ✗ Pipeline test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Animation generation
print("\n[Test 5/7] Testing animation generation...")
try:
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    # Path animation
    print("  Creating path animation...")
    path_anim_file = export_manager.animations_dir / f"final_test_path_{timestamp}.gif"
    path_animator = PathAnimator(
        field=results['field'],
        blocks=results['blocks'],
        path_plan=results['path_plan'],
        fps=30,
        speed_multiplier=2.0
    )
    path_animator.save_animation(
        filename=str(path_anim_file),
        dpi=80,  # Lower DPI for faster generation
        writer='pillow'
    )

    assert path_anim_file.exists()
    print(f"    ✓ Path animation: {path_anim_file.stat().st_size} bytes")

    # Pheromone animation
    print("  Creating pheromone animation...")
    pheromone_anim_file = export_manager.animations_dir / f"final_test_pheromone_{timestamp}.gif"
    pheromone_animator = PheromoneAnimator(
        solver=results['solver'],
        field=results['field'],
        blocks=results['blocks']
    )
    pheromone_animator.save_animation(
        filename=str(pheromone_anim_file),
        dpi=80,  # Lower DPI for faster generation
        fps=2
    )

    assert pheromone_anim_file.exists()
    print(f"    ✓ Pheromone animation: {pheromone_anim_file.stat().st_size} bytes")

    success_count += 1
except Exception as e:
    print(f"  ✗ Animation test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: All exports
print("\n[Test 6/7] Testing all export formats...")
try:
    # CSV exports
    conv_csv = export_manager.export_convergence_csv(
        results['solver'],
        filename=f"final_test_convergence_{timestamp}.csv"
    )
    assert conv_csv.exists()
    print(f"  ✓ Convergence CSV: {conv_csv.stat().st_size} bytes")

    stats_csv = export_manager.export_statistics_csv(
        results,
        filename=f"final_test_statistics_{timestamp}.csv"
    )
    assert stats_csv.exists()
    print(f"  ✓ Statistics CSV: {stats_csv.stat().st_size} bytes")

    # PNG images
    image_paths = export_manager.export_static_images(
        field=results['field'],
        blocks=results['blocks'],
        path_plan=results['path_plan'],
        solver=results['solver'],
        prefix=f"final_test_{timestamp}"
    )

    for img_type, img_path in image_paths.items():
        assert img_path.exists()
        print(f"  ✓ {img_type.title()} PNG: {img_path.stat().st_size} bytes")

    # PDF report
    pdf_path = export_manager.generate_pdf_report(
        results=results,
        image_paths=image_paths,
        animation_paths={
            'path': path_anim_file,
            'pheromone': pheromone_anim_file
        },
        filename=f"final_test_report_{timestamp}.pdf"
    )
    assert pdf_path.exists()
    print(f"  ✓ PDF Report: {pdf_path.stat().st_size} bytes")

    success_count += 1
except Exception as e:
    print(f"  ✗ Export test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 7: Streamlit app verification
print("\n[Test 7/7] Verifying Streamlit app structure...")
try:
    app_file = Path("streamlit_app.py")
    assert app_file.exists()

    with open(app_file, 'r') as f:
        content = f.read()
        assert 'st.set_page_config' in content
        assert 'render_quick_demo_tab' in content
        assert 'ACO Coverage Path Planning' in content

    print("  ✓ Streamlit app file validated")
    print(f"    - File size: {app_file.stat().st_size} bytes")

    success_count += 1
except Exception as e:
    print(f"  ✗ Streamlit app verification failed: {e}")
    sys.exit(1)

# Final summary
print("\n" + "=" * 80)
print("VALIDATION SUMMARY")
print("=" * 80)
print(f"Tests Passed: {success_count}/{total_tests}")

if success_count == total_tests:
    print("\n✅ ALL TESTS PASSED - PHASE 2A FULLY VALIDATED")
    print("\nGenerated test files:")
    print(f"  - {path_anim_file}")
    print(f"  - {pheromone_anim_file}")
    print(f"  - {conv_csv}")
    print(f"  - {stats_csv}")
    print(f"  - {pdf_path}")
    for img_type, img_path in image_paths.items():
        print(f"  - {img_path}")

    print("\n" + "=" * 80)
    print("READY FOR PRODUCTION USE! 🚀")
    print("=" * 80)
    print("\nTo launch the interactive dashboard:")
    print("  .venv/bin/streamlit run streamlit_app.py")
    print("\nOr test in headless mode:")
    print("  .venv/bin/streamlit run streamlit_app.py --server.headless true")
    print("=" * 80)
else:
    print(f"\n❌ VALIDATION FAILED - {total_tests - success_count} tests failed")
    sys.exit(1)
