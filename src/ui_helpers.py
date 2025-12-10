"""
UI Helper Functions for Baby Timeline
Utilities for loading external assets and styling.
"""

import streamlit as st
import os
from pathlib import Path


def load_css(file_path: str = "assets/styles.css") -> None:
    """
    Load external CSS file into Streamlit application.

    Args:
        file_path: Path to CSS file relative to project root

    Usage:
        from src.ui_helpers import load_css
        load_css()  # Loads default assets/styles.css
        load_css("assets/custom.css")  # Load custom CSS file
    """
    # Get the project root directory (parent of src/)
    project_root = Path(__file__).parent.parent
    css_file = project_root / file_path

    if not css_file.exists():
        st.warning(f"⚠️ CSS file not found: {file_path}")
        return

    try:
        with open(css_file, 'r', encoding='utf-8') as f:
            css_content = f.read()
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"❌ Failed to load CSS: {str(e)}")
