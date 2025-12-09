"""
Database Module for Baby Timeline
Handles CRUD operations for measurements and other database entities.
"""

import streamlit as st
from supabase import Client
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple


# ============================================================================
# Measurements CRUD Operations
# ============================================================================

def add_measurement(
    supabase: Client,
    baby_id: str,
    measurement_date: date,
    weight_kg: Optional[float] = None,
    height_cm: Optional[float] = None,
    notes: str = "",
    user_id: Optional[str] = None
) -> Tuple[bool, str, Optional[str]]:
    """
    Add a new measurement to the database.

    Args:
        supabase: Authenticated Supabase client
        baby_id: UUID of the baby
        measurement_date: Date of measurement
        weight_kg: Weight in kilograms (optional)
        height_cm: Height in centimeters (optional)
        notes: Optional notes (e.g., "Measured at doctor's office")
        user_id: User ID of recorder

    Returns:
        Tuple of (success: bool, message: str, measurement_id: str or None)

    Validation:
        - At least one of weight or height must be provided
        - Weight: 0.5 - 50 kg (reasonable baby/toddler range)
        - Height: 30 - 200 cm (reasonable baby/toddler range)

    Example:
        success, msg, id = add_measurement(
            supabase, baby_id, date.today(), weight_kg=8.2, height_cm=72.5
        )
    """
    try:
        # Validate: At least one measurement must be provided
        if weight_kg is None and height_cm is None:
            return False, "❌ Please enter at least weight or height", None

        # Validate weight range
        if weight_kg is not None and (weight_kg < 0.5 or weight_kg > 50):
            return False, "❌ Weight must be between 0.5 and 50 kg", None

        # Validate height range
        if height_cm is not None and (height_cm < 30 or height_cm > 200):
            return False, "❌ Height must be between 30 and 200 cm", None

        # Prepare data
        measurement_data = {
            "baby_id": baby_id,
            "measurement_date": measurement_date.strftime("%Y-%m-%d"),
            "weight_kg": weight_kg,
            "height_cm": height_cm,
            "notes": notes[:500] if notes else None,  # Enforce 500 char limit
            "recorded_by": user_id
        }

        # Insert into database
        result = supabase.table("measurements").insert(measurement_data).execute()

        if not result.data:
            raise Exception("Database insert failed - no data returned")

        measurement_id = result.data[0]["measurement_id"]

        # Build success message
        parts = []
        if weight_kg:
            parts.append(f"⚖️ Weight: {weight_kg} kg")
        if height_cm:
            parts.append(f"📏 Height: {height_cm} cm")

        success_msg = f"✅ Measurement recorded!\n\n{' | '.join(parts)}"

        return True, success_msg, measurement_id

    except Exception as e:
        error_msg = str(e)

        # Provide helpful error messages
        if "violates row-level security" in error_msg.lower():
            return False, "❌ Permission denied. Please log in as admin.", None
        elif "foreign key" in error_msg.lower():
            return False, "❌ Baby profile not found. Please create one first.", None
        else:
            return False, f"❌ Error saving measurement: {error_msg}", None


def get_measurements(
    supabase: Client,
    baby_id: str,
    limit: Optional[int] = None,
    order_by: str = "measurement_date",
    ascending: bool = False
) -> List[Dict]:
    """
    Get all measurements for a baby.

    Args:
        supabase: Authenticated Supabase client
        baby_id: UUID of the baby
        limit: Maximum number of records to return (None = all)
        order_by: Field to sort by (default: measurement_date)
        ascending: Sort order (False = newest first)

    Returns:
        List of measurement dictionaries

    Example:
        measurements = get_measurements(supabase, baby_id, limit=10)
        for m in measurements:
            print(f"{m['measurement_date']}: {m['weight_kg']} kg")
    """
    try:
        query = supabase.table("measurements") \
            .select("*") \
            .eq("baby_id", baby_id) \
            .order(order_by, desc=not ascending)

        if limit:
            query = query.limit(limit)

        result = query.execute()

        return result.data if result.data else []

    except Exception as e:
        print(f"Error fetching measurements: {e}")
        return []


def get_measurement_by_id(
    supabase: Client,
    measurement_id: str
) -> Optional[Dict]:
    """
    Get a single measurement by ID.

    Args:
        supabase: Authenticated Supabase client
        measurement_id: UUID of the measurement

    Returns:
        Measurement dictionary or None if not found
    """
    try:
        result = supabase.table("measurements") \
            .select("*") \
            .eq("measurement_id", measurement_id) \
            .execute()

        return result.data[0] if result.data else None

    except Exception as e:
        print(f"Error fetching measurement: {e}")
        return None


def update_measurement(
    supabase: Client,
    measurement_id: str,
    weight_kg: Optional[float] = None,
    height_cm: Optional[float] = None,
    notes: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Update an existing measurement.

    Args:
        supabase: Authenticated Supabase client
        measurement_id: UUID of the measurement
        weight_kg: New weight (None = no change)
        height_cm: New height (None = no change)
        notes: New notes (None = no change)

    Returns:
        Tuple of (success: bool, message: str)

    Note:
        Only updates fields that are provided (not None).
        Date cannot be updated (create new measurement instead).
    """
    try:
        # Build update data (only include provided fields)
        update_data = {}

        if weight_kg is not None:
            if weight_kg < 0.5 or weight_kg > 50:
                return False, "❌ Weight must be between 0.5 and 50 kg"
            update_data["weight_kg"] = weight_kg

        if height_cm is not None:
            if height_cm < 30 or height_cm > 200:
                return False, "❌ Height must be between 30 and 200 cm"
            update_data["height_cm"] = height_cm

        if notes is not None:
            update_data["notes"] = notes[:500]

        if not update_data:
            return False, "❌ No changes to update"

        # Update database
        result = supabase.table("measurements") \
            .update(update_data) \
            .eq("measurement_id", measurement_id) \
            .execute()

        if not result.data:
            return False, "❌ Measurement not found or permission denied"

        return True, "✅ Measurement updated successfully"

    except Exception as e:
        return False, f"❌ Update failed: {str(e)}"


def delete_measurement(
    supabase: Client,
    measurement_id: str
) -> Tuple[bool, str]:
    """
    Delete a measurement from the database.

    Args:
        supabase: Authenticated Supabase client
        measurement_id: UUID of the measurement

    Returns:
        Tuple of (success: bool, message: str)

    Note:
        RLS policies ensure only the baby's admin can delete.
    """
    try:
        result = supabase.table("measurements") \
            .delete() \
            .eq("measurement_id", measurement_id) \
            .execute()

        if not result.data:
            return False, "❌ Measurement not found or permission denied"

        return True, "✅ Measurement deleted successfully"

    except Exception as e:
        return False, f"❌ Delete failed: {str(e)}"


def get_measurements_count(supabase: Client, baby_id: str) -> int:
    """
    Get total count of measurements for a baby.

    Args:
        supabase: Authenticated Supabase client
        baby_id: UUID of the baby

    Returns:
        Count of measurements
    """
    try:
        result = supabase.table("measurements") \
            .select("measurement_id", count="exact") \
            .eq("baby_id", baby_id) \
            .execute()

        return result.count or 0

    except Exception as e:
        print(f"Error counting measurements: {e}")
        return 0


def get_latest_measurement(
    supabase: Client,
    baby_id: str
) -> Optional[Dict]:
    """
    Get the most recent measurement for a baby.

    Args:
        supabase: Authenticated Supabase client
        baby_id: UUID of the baby

    Returns:
        Latest measurement dictionary or None

    Use case:
        Display current weight/height on dashboard
    """
    measurements = get_measurements(supabase, baby_id, limit=1, ascending=False)
    return measurements[0] if measurements else None


def get_measurements_by_date_range(
    supabase: Client,
    baby_id: str,
    start_date: date,
    end_date: date
) -> List[Dict]:
    """
    Get measurements within a date range.

    Args:
        supabase: Authenticated Supabase client
        baby_id: UUID of the baby
        start_date: Start date (inclusive)
        end_date: End date (inclusive)

    Returns:
        List of measurements in date range

    Use case:
        Filter growth chart to specific time period
    """
    try:
        result = supabase.table("measurements") \
            .select("*") \
            .eq("baby_id", baby_id) \
            .gte("measurement_date", start_date.strftime("%Y-%m-%d")) \
            .lte("measurement_date", end_date.strftime("%Y-%m-%d")) \
            .order("measurement_date", desc=False) \
            .execute()

        return result.data if result.data else []

    except Exception as e:
        print(f"Error fetching measurements by date range: {e}")
        return []


# ============================================================================
# Baby Profile Operations
# ============================================================================

def get_baby_info(supabase: Client, baby_id: str) -> Optional[Dict]:
    """
    Get baby profile information.

    Args:
        supabase: Authenticated Supabase client
        baby_id: UUID of the baby

    Returns:
        Baby dictionary or None if not found

    Baby dict contains:
        - baby_id: UUID
        - name: str
        - birthdate: date string (YYYY-MM-DD)
        - profile_photo_url: str or None
        - created_by: UUID
        - created_at: timestamp
    """
    try:
        result = supabase.table("babies") \
            .select("*") \
            .eq("baby_id", baby_id) \
            .execute()

        return result.data[0] if result.data else None

    except Exception as e:
        print(f"Error fetching baby info: {e}")
        return None


def calculate_age(birthdate: date) -> Dict[str, int]:
    """
    Calculate age from birthdate.

    Args:
        birthdate: Baby's birthdate

    Returns:
        Dict with keys: years, months, days, total_days

    Example:
        age = calculate_age(date(2024, 6, 1))
        # Returns: {"years": 0, "months": 6, "days": 9, "total_days": 191}
    """
    today = date.today()
    total_days = (today - birthdate).days

    years = total_days // 365
    remaining_days = total_days % 365
    months = remaining_days // 30
    days = remaining_days % 30

    return {
        "years": years,
        "months": months,
        "days": days,
        "total_days": total_days
    }


def format_age(birthdate: date) -> str:
    """
    Format age as human-readable string.

    Args:
        birthdate: Baby's birthdate

    Returns:
        Formatted age string

    Examples:
        "3 days old"
        "2 weeks old"
        "3 months old"
        "1 year, 2 months old"
    """
    age = calculate_age(birthdate)

    if age["total_days"] < 7:
        return f"{age['total_days']} day{'s' if age['total_days'] != 1 else ''} old"
    elif age["total_days"] < 60:
        weeks = age["total_days"] // 7
        return f"{weeks} week{'s' if weeks != 1 else ''} old"
    elif age["years"] == 0:
        return f"{age['months']} month{'s' if age['months'] != 1 else ''} old"
    else:
        if age["months"] == 0:
            return f"{age['years']} year{'s' if age['years'] != 1 else ''} old"
        else:
            return f"{age['years']} year{'s' if age['years'] != 1 else ''}, {age['months']} month{'s' if age['months'] != 1 else ''} old"


# ============================================================================
# Statistics and Analytics
# ============================================================================

def get_growth_statistics(supabase: Client, baby_id: str) -> Dict:
    """
    Calculate growth statistics for a baby.

    Args:
        supabase: Authenticated Supabase client
        baby_id: UUID of the baby

    Returns:
        Dict with statistics:
        - total_measurements: int
        - first_measurement_date: str or None
        - latest_measurement_date: str or None
        - weight_change_kg: float or None (first to latest)
        - height_change_cm: float or None (first to latest)
        - avg_weight_kg: float or None
        - avg_height_cm: float or None

    Use case:
        Display summary stats on dashboard
    """
    try:
        measurements = get_measurements(supabase, baby_id, ascending=True)

        if not measurements:
            return {
                "total_measurements": 0,
                "first_measurement_date": None,
                "latest_measurement_date": None,
                "weight_change_kg": None,
                "height_change_cm": None,
                "avg_weight_kg": None,
                "avg_height_cm": None
            }

        first = measurements[0]
        latest = measurements[-1]

        # Calculate changes
        weight_change = None
        if first.get("weight_kg") and latest.get("weight_kg"):
            weight_change = latest["weight_kg"] - first["weight_kg"]

        height_change = None
        if first.get("height_cm") and latest.get("height_cm"):
            height_change = latest["height_cm"] - first["height_cm"]

        # Calculate averages
        weights = [m["weight_kg"] for m in measurements if m.get("weight_kg")]
        heights = [m["height_cm"] for m in measurements if m.get("height_cm")]

        avg_weight = sum(weights) / len(weights) if weights else None
        avg_height = sum(heights) / len(heights) if heights else None

        return {
            "total_measurements": len(measurements),
            "first_measurement_date": first["measurement_date"],
            "latest_measurement_date": latest["measurement_date"],
            "weight_change_kg": round(weight_change, 2) if weight_change else None,
            "height_change_cm": round(height_change, 1) if height_change else None,
            "avg_weight_kg": round(avg_weight, 2) if avg_weight else None,
            "avg_height_cm": round(avg_height, 1) if avg_height else None
        }

    except Exception as e:
        print(f"Error calculating growth statistics: {e}")
        return {
            "total_measurements": 0,
            "first_measurement_date": None,
            "latest_measurement_date": None,
            "weight_change_kg": None,
            "height_change_cm": None,
            "avg_weight_kg": None,
            "avg_height_cm": None
        }
