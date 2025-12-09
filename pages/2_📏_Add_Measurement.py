"""
Add Measurement Page - Baby Timeline
Allows admins to record height and weight measurements.
"""

import streamlit as st
from datetime import datetime, date
from src.auth import require_auth, get_supabase_client, get_user_id
from src.database import (
    add_measurement,
    get_measurements,
    delete_measurement,
    get_measurements_count,
    get_latest_measurement,
    get_baby_info,
    format_age,
    get_growth_statistics
)

# ============================================================================
# Page Configuration
# ============================================================================
st.set_page_config(
    page_title="Add Measurement - Baby Timeline",
    page_icon="📏",
    layout="wide"
)

# Require authentication (admin only)
require_auth()

# ============================================================================
# Main Page
# ============================================================================

st.title("📏 Add Measurement")
st.write("Track your baby's growth over time")

try:
    supabase = get_supabase_client()

    # ========================================================================
    # Step 1: Get baby info
    # ========================================================================
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
    # Step 2: Show statistics dashboard
    # ========================================================================
    stats = get_growth_statistics(supabase, baby_id)
    latest = get_latest_measurement(supabase, baby_id)

    st.subheader(f"{baby_name}'s Growth Stats")
    st.caption(f"👶 {format_age(baby_birthdate)}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Measurements", stats["total_measurements"])

    with col2:
        if latest and latest.get("weight_kg"):
            weight_change = stats["weight_change_kg"]
            delta = f"+{weight_change} kg" if weight_change else None
            st.metric("Latest Weight", f"{latest['weight_kg']} kg", delta=delta)
        else:
            st.metric("Latest Weight", "—")

    with col3:
        if latest and latest.get("height_cm"):
            height_change = stats["height_change_cm"]
            delta = f"+{height_change} cm" if height_change else None
            st.metric("Latest Height", f"{latest['height_cm']} cm", delta=delta)
        else:
            st.metric("Latest Height", "—")

    with col4:
        if stats["latest_measurement_date"]:
            last_date = datetime.strptime(stats["latest_measurement_date"], "%Y-%m-%d")
            days_ago = (datetime.now().date() - last_date.date()).days
            if days_ago == 0:
                st.metric("Last Recorded", "Today")
            elif days_ago == 1:
                st.metric("Last Recorded", "Yesterday")
            else:
                st.metric("Last Recorded", f"{days_ago} days ago")
        else:
            st.metric("Last Recorded", "Never")

    st.divider()

    # ========================================================================
    # Step 3: Add measurement form
    # ========================================================================

    st.subheader("Record New Measurement")

    with st.form("add_measurement_form", clear_on_submit=True):
        col_date, col_weight, col_height = st.columns(3)

        with col_date:
            measurement_date = st.date_input(
                "Date",
                value=datetime.now(),
                min_value=baby_birthdate,
                max_value=datetime.now(),
                help="When was this measurement taken?"
            )

        with col_weight:
            weight_kg = st.number_input(
                "Weight (kg)",
                min_value=0.0,
                max_value=50.0,
                step=0.1,
                format="%.1f",
                value=0.0,
                help="Leave as 0 if not measured"
            )

        with col_height:
            height_cm = st.number_input(
                "Height (cm)",
                min_value=0.0,
                max_value=200.0,
                step=0.5,
                format="%.1f",
                value=0.0,
                help="Leave as 0 if not measured"
            )

        notes = st.text_area(
            "Notes (optional)",
            max_chars=500,
            placeholder="e.g., Measured at 6-month checkup",
            help="Add any relevant context"
        )

        # Character counter
        if notes:
            st.caption(f"{len(notes)}/500 characters")

        submitted = st.form_submit_button(
            "💾 Save Measurement",
            type="primary",
            use_container_width=True
        )

    # Handle form submission OUTSIDE the form
    if submitted:
        # Convert 0.0 to None (means not measured)
        weight = weight_kg if weight_kg > 0 else None
        height = height_cm if height_cm > 0 else None

        if weight is None and height is None:
            st.error("❌ Please enter at least weight or height")
        else:
            with st.spinner("Saving measurement..."):
                success, message, measurement_id = add_measurement(
                    supabase=supabase,
                    baby_id=baby_id,
                    measurement_date=measurement_date,
                    weight_kg=weight,
                    height_cm=height,
                    notes=notes,
                    user_id=get_user_id()
                )

            if success:
                st.success(message)
                st.balloons()

                # Show navigation links (page_link works outside forms)
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.page_link("pages/2_📏_Add_Measurement.py", label="📏 Add Another", icon="➕")
                with col_b:
                    st.page_link("app.py", label="👀 View Timeline", icon="🏠")
                with col_c:
                    st.page_link("pages/3_📊_Growth_Chart.py", label="📊 Growth Chart", icon="📈")

            else:
                st.error(message)

    # ========================================================================
    # Step 4: Measurement history with edit/delete
    # ========================================================================

    st.divider()

    st.subheader("📊 Measurement History")

    measurements = get_measurements(supabase, baby_id, limit=20)

    if measurements:
        st.caption(f"Showing last {len(measurements)} measurements (newest first)")

        # Create table headers
        col_date, col_weight, col_height, col_notes, col_actions = st.columns([2, 2, 2, 3, 1])

        with col_date:
            st.markdown("**Date**")
        with col_weight:
            st.markdown("**Weight**")
        with col_height:
            st.markdown("**Height**")
        with col_notes:
            st.markdown("**Notes**")
        with col_actions:
            st.markdown("**Actions**")

        st.divider()

        # Display each measurement
        for measurement in measurements:
            col_date, col_weight, col_height, col_notes, col_actions = st.columns([2, 2, 2, 3, 1])

            with col_date:
                m_date = datetime.strptime(measurement["measurement_date"], "%Y-%m-%d")
                st.write(m_date.strftime("%b %d, %Y"))

            with col_weight:
                if measurement.get("weight_kg"):
                    st.write(f"⚖️ {measurement['weight_kg']} kg")
                else:
                    st.caption("—")

            with col_height:
                if measurement.get("height_cm"):
                    st.write(f"📏 {measurement['height_cm']} cm")
                else:
                    st.caption("—")

            with col_notes:
                if measurement.get("notes"):
                    # Truncate long notes
                    notes_text = measurement["notes"]
                    if len(notes_text) > 50:
                        notes_text = notes_text[:50] + "..."
                    st.caption(notes_text)
                else:
                    st.caption("—")

            with col_actions:
                # Delete button
                if st.button("🗑️", key=f"delete_{measurement['measurement_id']}", help="Delete measurement"):
                    success, message = delete_measurement(supabase, measurement["measurement_id"])
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

            st.divider()

        # Show pagination hint if there are more measurements
        total_count = get_measurements_count(supabase, baby_id)
        if total_count > len(measurements):
            st.caption(f"📋 Showing {len(measurements)} of {total_count} measurements")

    else:
        st.info("""
        📏 **No measurements recorded yet!**

        Get started by:
        1. Fill in the form above with weight and/or height
        2. Add optional notes (e.g., "6-month checkup")
        3. Click "Save Measurement"

        Your measurements will appear here and in the timeline.
        """)

    # ========================================================================
    # Step 5: Tips and guidelines
    # ========================================================================

    st.divider()

    with st.expander("💡 Tips for Accurate Measurements"):
        st.markdown("""
        ### Weight Measurement

        **For newborns (0-3 months):**
        - Use a baby scale (accurate to 10g)
        - Weigh before feeding (morning is best)
        - Remove diaper and clothes
        - Average range: 2.5 - 6 kg

        **For babies (3-12 months):**
        - Use baby scale or adult scale (holding baby minus adult weight)
        - Consistent time of day (morning recommended)
        - Average range: 6 - 11 kg

        **For toddlers (1-3 years):**
        - Can use adult scale
        - Remove heavy clothing and shoes
        - Average range: 9 - 15 kg

        ---

        ### Height Measurement

        **For babies (0-12 months):**
        - Measure lying down (length)
        - Use measuring mat or tape measure
        - Gently straighten legs
        - Average range: 50 - 75 cm

        **For toddlers (1-3 years):**
        - Can measure standing (height)
        - Stand against wall without shoes
        - Look straight ahead
        - Average range: 75 - 95 cm

        ---

        ### How Often to Measure?

        - **0-6 months:** Every 2 weeks (rapid growth)
        - **6-12 months:** Monthly
        - **1-3 years:** Every 2-3 months
        - **Checkups:** Always record doctor's measurements

        ---

        ### Notes Field Ideas

        Use notes to record:
        - Where measured (home, doctor's office)
        - Time of day
        - Clothing worn (affects weight)
        - Health status (recent illness)
        - Milestones (started walking, etc.)
        - Percentile from doctor (e.g., "50th percentile")

        **Example:** "6-month checkup at pediatrician - 50th percentile for weight, healthy!"
        """)

except ValueError as e:
    # Environment not configured
    st.error(str(e))
    st.info("👉 **Setup required:** Follow the guide in `SUPABASE_SETUP.md`")

except Exception as e:
    st.error(f"❌ Error loading measurement page: {str(e)}")
    st.exception(e)  # Show full error in development

# ============================================================================
# Footer
# ============================================================================

st.divider()
st.caption("📊 **Tip:** Regular measurements help track growth patterns and identify any concerns early.")
