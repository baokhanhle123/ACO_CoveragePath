"""
ACO Coverage Path Planning - Interactive Dashboard

Main Streamlit application providing interactive visualization
and demonstration of the ACO-based coverage path planning system.
"""

import streamlit as st
from pathlib import Path

# Configure page
st.set_page_config(
    page_title="ACO Coverage Path Planning",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar
with st.sidebar:
    st.title("🚜 ACO Coverage Path Planning")
    st.markdown("---")

    st.markdown("### About")
    st.info(
        "**Ant Colony Optimization** for agricultural coverage path planning. "
        "This dashboard demonstrates the complete pipeline from field decomposition "
        "to optimized coverage path generation."
    )

    st.markdown("### Project Info")
    st.markdown("**Algorithm**: Ant Colony Optimization (ACO)")
    st.markdown("**Application**: Agricultural Coverage Planning")
    st.markdown("**Features**:")
    st.markdown("- Field decomposition")
    st.markdown("- Block sequencing optimization")
    st.markdown("- Path generation")
    st.markdown("- Interactive visualization")

    st.markdown("---")
    st.markdown("### Navigation")
    st.markdown("Use the **Quick Demo** tab to run pre-configured scenarios.")

    st.markdown("---")
    st.caption("© 2025 ACO Coverage Path Planning Project")

# Main content
st.title("🚜 ACO Coverage Path Planning Dashboard")
st.markdown("Interactive demonstration and analysis tool for coverage path planning using Ant Colony Optimization")

# Single tab for now (Phase 2A)
tab1 = st.tabs(["📊 Quick Demo"])[0]

with tab1:
    from src.dashboard.quick_demo import render_quick_demo_tab
    render_quick_demo_tab()
