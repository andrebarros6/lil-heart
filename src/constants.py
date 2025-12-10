"""
Constants and Configuration for Baby Timeline
Centralized location for all magic numbers and configuration values.
"""

# ============================================================================
# Image and Storage Configuration
# ============================================================================

# Image processing
DEFAULT_MAX_IMAGE_WIDTH = 1920  # Maximum width for uploaded photos (pixels)
DEFAULT_IMAGE_QUALITY = 85  # JPEG quality (0-100, higher = better quality)

# Storage limits
MAX_FILE_SIZE_MB = 10  # Maximum upload size per photo
AVG_OPTIMIZED_PHOTO_SIZE_MB = 1.0  # Average size after optimization
STORAGE_LIMIT_FREE_TIER_MB = 1000  # Supabase free tier limit

# Signed URL expiration
SIGNED_URL_EXPIRY_SECONDS = 315360000  # 10 years (for private bucket URLs)

# ============================================================================
# Measurement Validation
# ============================================================================

# Weight validation (kg)
MIN_WEIGHT_KG = 0.5  # Minimum realistic baby weight
MAX_WEIGHT_KG = 50.0  # Maximum realistic baby weight

# Height validation (cm)
MIN_HEIGHT_CM = 30  # Minimum realistic baby height
MAX_HEIGHT_CM = 200  # Maximum realistic baby height

# ============================================================================
# Text Input Limits
# ============================================================================

MAX_NOTES_LENGTH = 500  # Maximum length for measurement notes
MAX_CAPTION_LENGTH = 500  # Maximum length for photo captions
MAX_FILENAME_LENGTH = 50  # Maximum length for uploaded filenames

# ============================================================================
# UI and Chart Configuration
# ============================================================================

# Plotly chart colors
CHART_COLOR_WEIGHT = "#4169E1"  # Royal blue for weight charts
CHART_COLOR_HEIGHT = "#32CD32"  # Lime green for height charts

# Timeline display
DEFAULT_TIMELINE_LIMIT = 50  # Number of items to fetch per timeline view
DEFAULT_RECENT_PHOTOS_LIMIT = 5  # Number of recent photos to display

# ============================================================================
# Session State Keys (prevents typos across the app)
# ============================================================================

SESSION_AUTHENTICATED = "authenticated"
SESSION_USER = "user"
SESSION_VIEWER_MODE = "viewer_mode"
SESSION_VIEWER_BABY_ID = "viewer_baby_id"
SESSION_VIEWER_AUTHENTICATED = "viewer_authenticated"

# ============================================================================
# Date and Time Configuration
# ============================================================================

# Date range filters (days)
DATE_RANGE_3_MONTHS = 90
DATE_RANGE_6_MONTHS = 180
DATE_RANGE_1_YEAR = 365

# ============================================================================
# Password and Security
# ============================================================================

MIN_PASSWORD_LENGTH = 4  # Minimum password length for share links
