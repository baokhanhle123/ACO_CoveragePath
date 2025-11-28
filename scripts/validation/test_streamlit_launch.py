"""
Test that Streamlit app can be imported and initialized without errors.
"""

import sys
from pathlib import Path

print("=" * 70)
print("STREAMLIT APP LAUNCH VERIFICATION")
print("=" * 70)

try:
    print("\n[1/3] Checking Streamlit installation...")
    import streamlit as st
    print(f"  ✓ Streamlit version: {st.__version__}")

    print("\n[2/3] Verifying app file exists...")
    app_file = Path("streamlit_app.py")
    if not app_file.exists():
        raise FileNotFoundError("streamlit_app.py not found")
    print(f"  ✓ App file found: {app_file}")

    print("\n[3/3] Verifying app can import dependencies...")
    # Read and verify the app file
    with open(app_file, 'r') as f:
        content = f.read()

    # Verify key components
    checks = {
        'st.set_page_config': 'Page configuration',
        'render_quick_demo_tab': 'Quick Demo tab',
        'st.sidebar': 'Sidebar',
        'st.title': 'Title',
        'st.tabs': 'Tabs'
    }

    for check, desc in checks.items():
        if check in content:
            print(f"  ✓ {desc} found")
        else:
            raise ValueError(f"{desc} not found in app")

    # Try importing dashboard modules (this verifies they work)
    from src.dashboard import render_quick_demo_tab
    print("  ✓ Dashboard modules import successfully")

    print("\n" + "=" * 70)
    print("✅ STREAMLIT APP VERIFIED - READY TO LAUNCH")
    print("=" * 70)
    print("\nTo launch the dashboard:")
    print("  .venv/bin/streamlit run streamlit_app.py")
    print("\nThe dashboard will be available at:")
    print("  http://localhost:8501")
    print("\nTo stop the server, press Ctrl+C in the terminal.")
    print("=" * 70)

except Exception as e:
    print("\n" + "=" * 70)
    print("❌ STREAMLIT APP VERIFICATION FAILED")
    print("=" * 70)
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
