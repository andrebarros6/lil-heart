"""
Growth Chart Page - Baby Timeline
Interactive visualization of baby's growth over time using Plotly.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from src.auth import is_authenticated, get_supabase_client, init_supabase
from src.database import get_measurements, format_age
from src.constants import (
    CHART_COLOR_WEIGHT,
    CHART_COLOR_HEIGHT,
    DATE_RANGE_3_MONTHS,
    DATE_RANGE_6_MONTHS,
    DATE_RANGE_1_YEAR
)

# ============================================================================
# Page Configuration
# ============================================================================
st.set_page_config(
    page_title="Growth Chart - Baby Timeline",
    page_icon="📊",
    layout="wide"
)

# ============================================================================
# Access Control - Allow both admins and viewers
# ============================================================================
is_admin = is_authenticated()
is_viewer = st.session_state.get("viewer_mode") and st.session_state.get("viewer_baby_id")

if not is_admin and not is_viewer:
    st.error("🔒 Access denied. Please log in or use a valid share link.")
    st.page_link("app.py", label="← Back to Main Page", icon="🏠")
    st.stop()

# ============================================================================
# Main Page
# ============================================================================

if is_viewer:
    st.title("📊 Growth Chart (View Only)")
else:
    st.title("📊 Growth Chart")

st.write("Visualize your baby's growth over time")

try:
    supabase = get_supabase_client() if is_admin else init_supabase()

    # ========================================================================
    # Step 1: Get baby info
    # ========================================================================
    if is_viewer:
        # Viewer: use baby_id from session
        baby_id = st.session_state["viewer_baby_id"]
        babies = supabase.table("babies").select("*").eq("baby_id", baby_id).execute()
    else:
        # Admin: get all babies (for MVP, just first one)
        babies = supabase.table("babies").select("*").execute()

    if not babies.data:
        st.error("❌ No baby profile found. Please create one from the main page.")
        st.page_link("app.py", label="← Back to Main Page", icon="🏠")
        st.stop()

    baby = babies.data[0]
    baby_id = baby["baby_id"]
    baby_name = baby["name"]
    baby_birthdate = datetime.strptime(baby["birthdate"], "%Y-%m-%d").date()

    # ========================================================================
    # Step 2: Fetch measurements
    # ========================================================================
    with st.spinner("Loading measurements..."):
        measurements_response = get_measurements(supabase, baby_id)
        measurements = measurements_response if isinstance(measurements_response, list) else measurements_response.data if hasattr(measurements_response, 'data') else []

    if not measurements:
        st.info("""
        📊 **No measurements yet!**

        Get started by:
        1. Click "📏 Add Measurement" in the sidebar
        2. Record your baby's weight and/or height
        3. Come back here to see the growth chart

        You need at least 2 measurements to see trends over time.
        """)

        col_a, col_b = st.columns(2)
        with col_a:
            st.page_link("pages/2_📏_Add_Measurement.py", label="📏 Add Measurement", icon="➕")
        with col_b:
            st.page_link("app.py", label="👀 View Timeline", icon="🏠")

        st.stop()

    # ========================================================================
    # Step 3: Convert to DataFrame and prepare data
    # ========================================================================
    df = pd.DataFrame(measurements)
    df["measurement_date"] = pd.to_datetime(df["measurement_date"])
    df = df.sort_values("measurement_date")

    # Calculate age at each measurement
    df["age_days"] = (df["measurement_date"] - pd.to_datetime(baby_birthdate)).dt.days

    st.subheader(f"{baby_name}'s Growth")
    st.caption(f"👶 {format_age(baby_birthdate)} | {len(measurements)} measurements recorded")

    # ========================================================================
    # Step 4: Chart controls
    # ========================================================================
    col_chart_type, col_date_range = st.columns([2, 2])

    with col_chart_type:
        chart_type = st.radio(
            "Chart Type",
            ["Weight", "Height", "Combined"],
            horizontal=True,
            help="Choose which measurements to display"
        )

    with col_date_range:
        date_range = st.selectbox(
            "Date Range",
            ["All time", "Last 3 months", "Last 6 months", "Last year"],
            help="Filter measurements by time period"
        )

    # Filter data based on date range
    today = datetime.now()
    if date_range == "Last 3 months":
        cutoff_date = today - timedelta(days=DATE_RANGE_3_MONTHS)
        df_filtered = df[df["measurement_date"] >= cutoff_date]
    elif date_range == "Last 6 months":
        cutoff_date = today - timedelta(days=DATE_RANGE_6_MONTHS)
        df_filtered = df[df["measurement_date"] >= cutoff_date]
    elif date_range == "Last year":
        cutoff_date = today - timedelta(days=DATE_RANGE_1_YEAR)
        df_filtered = df[df["measurement_date"] >= cutoff_date]
    else:  # All time
        df_filtered = df

    if len(df_filtered) == 0:
        st.warning(f"⚠️ No measurements found in {date_range}. Try selecting 'All time'.")
        st.stop()

    st.divider()

    # ========================================================================
    # Step 5: Create Plotly charts
    # ========================================================================

    if chart_type == "Weight":
        # ==================== Weight Chart ====================
        weight_data = df_filtered[df_filtered["weight_kg"].notna()]

        if len(weight_data) == 0:
            st.warning("⚠️ No weight measurements recorded yet.")
        else:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=weight_data["measurement_date"],
                y=weight_data["weight_kg"],
                mode="lines+markers",
                name="Weight",
                line=dict(color=CHART_COLOR_WEIGHT, width=3),
                marker=dict(size=10, symbol="circle"),
                hovertemplate="<b>%{x|%b %d, %Y}</b><br>" +
                             "Weight: %{y:.1f} kg<br>" +
                             "<extra></extra>"
            ))

            fig.update_layout(
                title=f"{baby_name}'s Weight Over Time",
                xaxis_title="Date",
                yaxis_title="Weight (kg)",
                hovermode="x unified",
                height=500,
                template="plotly_white",
                font=dict(size=12)
            )

            st.plotly_chart(fig, use_container_width=True)

            # Statistics
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                st.metric("Latest", f"{weight_data.iloc[-1]['weight_kg']:.1f} kg")
            with col_stat2:
                first_weight = weight_data.iloc[0]["weight_kg"]
                latest_weight = weight_data.iloc[-1]["weight_kg"]
                change = latest_weight - first_weight
                st.metric("Total Change", f"{change:+.1f} kg", delta=f"{change:.1f} kg")
            with col_stat3:
                avg_weight = weight_data["weight_kg"].mean()
                st.metric("Average", f"{avg_weight:.1f} kg")

    elif chart_type == "Height":
        # ==================== Height Chart ====================
        height_data = df_filtered[df_filtered["height_cm"].notna()]

        if len(height_data) == 0:
            st.warning("⚠️ No height measurements recorded yet.")
        else:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=height_data["measurement_date"],
                y=height_data["height_cm"],
                mode="lines+markers",
                name="Height",
                line=dict(color=CHART_COLOR_HEIGHT, width=3),
                marker=dict(size=10, symbol="square"),
                hovertemplate="<b>%{x|%b %d, %Y}</b><br>" +
                             "Height: %{y:.1f} cm<br>" +
                             "<extra></extra>"
            ))

            fig.update_layout(
                title=f"{baby_name}'s Height Over Time",
                xaxis_title="Date",
                yaxis_title="Height (cm)",
                hovermode="x unified",
                height=500,
                template="plotly_white",
                font=dict(size=12)
            )

            st.plotly_chart(fig, use_container_width=True)

            # Statistics
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                st.metric("Latest", f"{height_data.iloc[-1]['height_cm']:.1f} cm")
            with col_stat2:
                first_height = height_data.iloc[0]["height_cm"]
                latest_height = height_data.iloc[-1]["height_cm"]
                change = latest_height - first_height
                st.metric("Total Change", f"{change:+.1f} cm", delta=f"{change:.1f} cm")
            with col_stat3:
                avg_height = height_data["height_cm"].mean()
                st.metric("Average", f"{avg_height:.1f} cm")

    else:  # Combined
        # ==================== Combined Chart (Dual Y-Axis) ====================
        weight_data = df_filtered[df_filtered["weight_kg"].notna()]
        height_data = df_filtered[df_filtered["height_cm"].notna()]

        if len(weight_data) == 0 and len(height_data) == 0:
            st.warning("⚠️ No measurements recorded yet.")
        else:
            fig = go.Figure()

            # Add weight trace (left Y-axis)
            if len(weight_data) > 0:
                fig.add_trace(go.Scatter(
                    x=weight_data["measurement_date"],
                    y=weight_data["weight_kg"],
                    mode="lines+markers",
                    name="Weight",
                    line=dict(color=CHART_COLOR_WEIGHT, width=3),
                    marker=dict(size=10, symbol="circle"),
                    yaxis="y1",
                    hovertemplate="<b>%{x|%b %d, %Y}</b><br>" +
                                 "Weight: %{y:.1f} kg<br>" +
                                 "<extra></extra>"
                ))

            # Add height trace (right Y-axis)
            if len(height_data) > 0:
                fig.add_trace(go.Scatter(
                    x=height_data["measurement_date"],
                    y=height_data["height_cm"],
                    mode="lines+markers",
                    name="Height",
                    line=dict(color=CHART_COLOR_HEIGHT, width=3),
                    marker=dict(size=10, symbol="square"),
                    yaxis="y2",
                    hovertemplate="<b>%{x|%b %d, %Y}</b><br>" +
                                 "Height: %{y:.1f} cm<br>" +
                                 "<extra></extra>"
                ))

            # Configure dual Y-axis layout
            fig.update_layout(
                title=f"{baby_name}'s Weight & Height Over Time",
                xaxis_title="Date",
                yaxis=dict(
                    title=dict(text="Weight (kg)", font=dict(color=CHART_COLOR_WEIGHT)),
                    tickfont=dict(color=CHART_COLOR_WEIGHT),
                    side="left"
                ),
                yaxis2=dict(
                    title=dict(text="Height (cm)", font=dict(color=CHART_COLOR_HEIGHT)),
                    tickfont=dict(color=CHART_COLOR_HEIGHT),
                    overlaying="y",
                    side="right"
                ),
                hovermode="x unified",
                height=500,
                template="plotly_white",
                font=dict(size=12),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )

            st.plotly_chart(fig, use_container_width=True)

            # Combined statistics
            col_weight, col_height = st.columns(2)

            with col_weight:
                if len(weight_data) > 0:
                    st.markdown("#### ⚖️ Weight")
                    col_w1, col_w2 = st.columns(2)
                    with col_w1:
                        st.metric("Latest", f"{weight_data.iloc[-1]['weight_kg']:.1f} kg")
                    with col_w2:
                        first_weight = weight_data.iloc[0]["weight_kg"]
                        latest_weight = weight_data.iloc[-1]["weight_kg"]
                        change = latest_weight - first_weight
                        st.metric("Change", f"{change:+.1f} kg")
                else:
                    st.info("📊 No weight data")

            with col_height:
                if len(height_data) > 0:
                    st.markdown("#### 📏 Height")
                    col_h1, col_h2 = st.columns(2)
                    with col_h1:
                        st.metric("Latest", f"{height_data.iloc[-1]['height_cm']:.1f} cm")
                    with col_h2:
                        first_height = height_data.iloc[0]["height_cm"]
                        latest_height = height_data.iloc[-1]["height_cm"]
                        change = latest_height - first_height
                        st.metric("Change", f"{change:+.1f} cm")
                else:
                    st.info("📊 No height data")

    # ========================================================================
    # Step 6: Data table (collapsible)
    # ========================================================================
    st.divider()

    with st.expander("📋 View Data Table", expanded=False):
        # Prepare display dataframe
        display_df = df_filtered[["measurement_date", "weight_kg", "height_cm", "notes"]].copy()
        display_df["measurement_date"] = display_df["measurement_date"].dt.strftime("%b %d, %Y")
        display_df.columns = ["Date", "Weight (kg)", "Height (cm)", "Notes"]

        # Replace NaN with em dash
        display_df = display_df.fillna("—")

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

        st.caption(f"Showing {len(display_df)} measurements")

    # ========================================================================
    # Step 7: Tips and insights
    # ========================================================================
    st.divider()

    with st.expander("💡 Tips for Tracking Growth"):
        st.markdown("""
        ### How to Use Growth Charts

        **What to look for:**
        - **Steady upward trend:** Baby should gain weight and height consistently
        - **Growth spurts:** Periods of rapid growth (steeper slope on chart)
        - **Plateaus:** Short flat periods are normal between spurts

        **Red flags (consult pediatrician):**
        - Sudden drop in weight or height
        - No growth for extended period (> 1 month for babies)
        - Weight loss without illness

        ---

        ### Measurement Frequency

        - **0-3 months:** Every 2 weeks (rapid growth phase)
        - **3-6 months:** Every 3 weeks
        - **6-12 months:** Monthly
        - **1-3 years:** Every 2-3 months
        - **Always:** At pediatrician checkups

        ---

        ### Average Growth Rates

        **Weight (first year):**
        - 0-3 months: ~150-200g/week
        - 3-6 months: ~100-150g/week
        - 6-12 months: ~50-100g/week

        **Height (first year):**
        - 0-6 months: ~2.5cm/month
        - 6-12 months: ~1.2cm/month

        **Note:** Every baby grows at their own pace. These are averages, not strict rules.

        ---

        ### Future Enhancement: WHO Percentiles

        We're planning to add WHO growth percentile curves so you can compare your baby's growth to global averages.
        This will show if your baby is in the 10th, 50th, 90th percentile, etc.
        """)

except ValueError as e:
    # Environment not configured
    st.error(str(e))
    st.info("👉 **Setup required:** Follow the guide in `SUPABASE_SETUP.md`")

except Exception as e:
    st.error(f"❌ Error loading growth chart: {str(e)}")
    st.exception(e)  # Show full error in development

# ============================================================================
# Footer
# ============================================================================

st.divider()
st.caption("📊 **Tip:** Regular measurements help identify growth patterns early. Aim for weekly measurements in the first 3 months.")
