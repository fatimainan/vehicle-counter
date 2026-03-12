"""
Configuration file for Vehicle Counting System
Contains all configurable parameters for the system
"""

# Video Input Configuration
VIDEO_SOURCE = 0  # 0 for webcam, or path to video file like "traffic.mp4"
FALLBACK_VIDEO = "traffic.mp4"  # Fallback video file if webcam fails

# Display and Output Configuration
SHOW_GUI = True  # Set to False for headless operation
SAVE_OUTPUT = True  # Set to True to save output video
OUTPUT_VIDEO_PATH = "output.mp4"
OUTPUT_FPS = 20  # FPS for output video

# Detection Parameters
MIN_CONTOUR_AREA = 1000  # Minimum area for vehicle detection (pixels)
MAX_CONTOUR_AREA = 50000  # Maximum area to filter out very large objects
BACKGROUND_HISTORY = 500  # Number of frames for MOG2 background model
BACKGROUND_THRESHOLD = 16  # Threshold for MOG2 background subtraction
DETECT_SHADOWS = True  # Whether to detect shadows in MOG2

# Counting Line Configuration
COUNTING_LINE_POSITION = 0.6  # Position of counting line (0.0 to 1.0 from top)
COUNTING_LINE_THICKNESS = 3
COUNTING_LINE_COLOR = (0, 255, 255)  # Yellow line

# Visual Configuration
BOUNDING_BOX_COLOR = (0, 255, 0)  # Green bounding boxes
CENTER_POINT_COLOR = (0, 0, 255)  # Red center points
TEXT_COLOR = (255, 255, 255)  # White text
TEXT_FONT = 1  # cv2.FONT_HERSHEY_SIMPLEX
TEXT_SCALE = 0.8
TEXT_THICKNESS = 2

# Tracking Configuration
MAX_TRACKING_DISTANCE = 50  # Maximum distance for tracking objects between frames
MIN_FRAMES_TO_COUNT = 3  # Minimum frames an object must be tracked before counting
