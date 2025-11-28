"""
Test script for dashboard components.

Verifies ConfigManager and ExportManager functionality before launching
the full Streamlit dashboard.
"""

import sys
from pathlib import Path

print("=" * 70)
print("DASHBOARD COMPONENTS TEST")
print("=" * 70)

# Test 1: ConfigManager
print("\n[Test 1] ConfigManager - Loading Scenarios")
print("-" * 70)

try:
    from src.dashboard import ConfigManager, ConfigurationError

    config_manager = ConfigManager()

    # Test all scenarios
    scenarios = ['small', 'medium', 'large']
    for scenario in scenarios:
        print(f"\nLoading '{scenario}' scenario...")
        config = config_manager.load_scenario(scenario)

        print(f"  ✓ Name: {config.name}")
        print(f"  ✓ Field: {config.field_config['width']}x{config.field_config['height']}m")
        print(f"  ✓ Obstacles: {len(config.field_config['obstacles'])}")
        print(f"  ✓ ACO Iterations: {config.aco_params['num_iterations']}")
        print(f"  ✓ ACO Ants: {config.aco_params['num_ants']}")

    print("\n✅ ConfigManager: ALL TESTS PASSED")

except Exception as e:
    print(f"\n❌ ConfigManager: FAILED - {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: ExportManager - Directory Creation
print("\n[Test 2] ExportManager - Directory Setup")
print("-" * 70)

try:
    from src.dashboard import ExportManager

    export_manager = ExportManager()

    # Check all directories exist
    dirs = [
        ('Animations', export_manager.animations_dir),
        ('Reports', export_manager.reports_dir),
        ('Data', export_manager.data_dir),
        ('Images', export_manager.images_dir)
    ]

    for name, dir_path in dirs:
        if dir_path.exists():
            print(f"  ✓ {name} directory: {dir_path}")
        else:
            raise FileNotFoundError(f"{name} directory not created: {dir_path}")

    print("\n✅ ExportManager: ALL TESTS PASSED")

except Exception as e:
    print(f"\n❌ ExportManager: FAILED - {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Quick Demo Pipeline - Import Test
print("\n[Test 3] Quick Demo Pipeline - Import Verification")
print("-" * 70)

try:
    from src.dashboard import run_complete_pipeline, render_quick_demo_tab

    print("  ✓ run_complete_pipeline imported successfully")
    print("  ✓ render_quick_demo_tab imported successfully")

    print("\n✅ Quick Demo Pipeline: ALL TESTS PASSED")

except Exception as e:
    print(f"\n❌ Quick Demo Pipeline: FAILED - {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Streamlit App - File Verification
print("\n[Test 4] Streamlit App - File Verification")
print("-" * 70)

try:
    app_file = Path("streamlit_app.py")

    if not app_file.exists():
        raise FileNotFoundError("streamlit_app.py not found")

    print(f"  ✓ Main app file: {app_file}")
    print(f"  ✓ File size: {app_file.stat().st_size} bytes")

    # Check if it imports without errors
    with open(app_file, 'r') as f:
        content = f.read()
        if 'render_quick_demo_tab' in content:
            print("  ✓ Quick Demo tab integration found")
        else:
            raise ValueError("Quick Demo tab integration not found")

    print("\n✅ Streamlit App: ALL TESTS PASSED")

except Exception as e:
    print(f"\n❌ Streamlit App: FAILED - {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Dependencies Check
print("\n[Test 5] Dependencies - Import Verification")
print("-" * 70)

try:
    import streamlit
    import plotly
    from fpdf import FPDF
    import pandas
    import matplotlib

    print(f"  ✓ streamlit: {streamlit.__version__}")
    print(f"  ✓ plotly: {plotly.__version__}")
    print(f"  ✓ fpdf2: installed")
    print(f"  ✓ pandas: {pandas.__version__}")
    print(f"  ✓ matplotlib: {matplotlib.__version__}")

    print("\n✅ Dependencies: ALL TESTS PASSED")

except Exception as e:
    print(f"\n❌ Dependencies: FAILED - {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print("✅ All component tests passed successfully!")
print("\nNext step: Launch Streamlit dashboard with:")
print("  streamlit run streamlit_app.py")
print("=" * 70)
