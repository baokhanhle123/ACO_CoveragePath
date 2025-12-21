"""
ACO Coverage Path Planning - Interactive Dashboard

Main Streamlit application providing interactive visualization
and demonstration of the ACO-based coverage path planning system.
"""

# Configure matplotlib for headless environment (Streamlit Cloud)
import matplotlib
matplotlib.use('Agg')  # Headless backend for Streamlit Cloud

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
    st.markdown("**Quick Demo**: Run pre-configured scenarios")
    st.markdown("**Stage 1**: Field geometry and obstacle classification")
    st.markdown("**Stage 2**: Boustrophedon decomposition")
    st.markdown("**Stage 3**: ACO path optimization")

    st.markdown("---")
    st.caption("© 2025 ACO Coverage Path Planning Project")

# Main content
st.title("🚜 ACO Coverage Path Planning Dashboard")
st.markdown("Interactive demonstration and analysis tool for coverage path planning using Ant Colony Optimization")

# Multi-tab interface for 3-stage visualization
tabs = st.tabs([
    "🚀 Quick Demo",
    "📐 Stage 1: Field Geometry",
    "🔲 Stage 2: Decomposition",
    "🎯 Stage 3: Path Optimization"
])

with tabs[0]:
    from src.dashboard.quick_demo import render_quick_demo_tab
    render_quick_demo_tab()

with tabs[1]:
    from src.dashboard.stage_tabs import render_stage1_tab
    render_stage1_tab()

with tabs[2]:
    from src.dashboard.stage_tabs import render_stage2_tab
    render_stage2_tab()

with tabs[3]:
    from src.dashboard.stage_tabs import render_stage3_tab
    render_stage3_tab()
