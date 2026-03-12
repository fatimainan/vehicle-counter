"""
Vehicle Counting System using OpenCV with MOG2 Background Subtraction
Real-time vehicle detection and counting with line-crossing logic
"""

import cv2
import numpy as np
import time
import os
from typing import List, Tuple, Optional, Dict
import config

class VehicleTracker:
    """Class to track individual vehicles across frames"""
    
    def __init__(self, center: Tuple[int, int], frame_id: int):
        self.centers = [center]  # History of center positions
        self.frame_ids = [frame_id]  # Frame IDs where this object was detected
        self.counted = False  # Whether this vehicle has been counted
        self.last_seen = frame_id
        
    def update(self, center: Tuple[int, int], frame_id: int):
        """Update tracker with new position"""
        self.centers.append(center)
        self.frame_ids.append(frame_id)
        self.last_seen = frame_id
        
        # Keep only recent history to save memory
        if len(self.centers) > 10:
            self.centers.pop(0)
            self.frame_ids.pop(0)
    
    def get_last_position(self) -> Tuple[int, int]:
        """Get the most recent position"""
        return self.centers[-1] if self.centers else (0, 0)
    
    def has_crossed_line(self, line_y: int) -> bool:
        """Check if vehicle has crossed the counting line"""
        if len(self.centers) < 2:
            return False
        
        # Check if the vehicle crossed from top to bottom
        prev_y = self.centers[-2][1]
        curr_y = self.centers[-1][1]
        
        return prev_y < line_y <= curr_y and not self.counted

class VehicleCountingSystem:
    """Main vehicle counting system class"""
    
    def __init__(self):
        # Initialize video capture
        self.cap = None
        self.video_writer = None
        
        # Initialize background subtractor
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=config.BACKGROUND_HISTORY,
            varThreshold=config.BACKGROUND_THRESHOLD,
            detectShadows=config.DETECT_SHADOWS
        )
        
        # Initialize tracking variables
        self.vehicle_trackers: List[VehicleTracker] = []
        self.vehicle_count = 0
        self.frame_id = 0
        
        # Performance tracking
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0
        
    def initialize_video_source(self) -> bool:
        """Initialize video source (webcam or file)"""
        try:
            # Try webcam first
            if isinstance(config.VIDEO_SOURCE, int):
                print(f"Attempting to open webcam (device {config.VIDEO_SOURCE})...")
                self.cap = cv2.VideoCapture(config.VIDEO_SOURCE)
                
                if not self.cap.isOpened():
                    print("Webcam not available, trying fallback video file...")
                    self.cap = cv2.VideoCapture(config.FALLBACK_VIDEO)
            else:
                # Use video file
                print(f"Opening video file: {config.VIDEO_SOURCE}")
                self.cap = cv2.VideoCapture(config.VIDEO_SOURCE)
            
            if not self.cap.isOpened():
                print("Error: Could not open video source")
                return False
            
            # Get video properties
            self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.input_fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            print(f"Video initialized: {self.frame_width}x{self.frame_height} @ {self.input_fps} FPS")
            
            # Calculate counting line position
            self.counting_line_y = int(self.frame_height * config.COUNTING_LINE_POSITION)
            
            return True
            
        except Exception as e:
            print(f"Error initializing video source: {str(e)}")
            return False
    
    def initialize_video_writer(self) -> bool:
        """Initialize video writer for output"""
        if not config.SAVE_OUTPUT:
            return True
        
        try:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(
                config.OUTPUT_VIDEO_PATH,
                fourcc,
                config.OUTPUT_FPS,
                (self.frame_width, self.frame_height)
            )
            
            if self.video_writer.isOpened():
                print(f"Output video writer initialized: {config.OUTPUT_VIDEO_PATH}")
                return True
            else:
                print("Warning: Could not initialize video writer")
                return False
                
        except Exception as e:
            print(f"Error initializing video writer: {str(e)}")
            return False
    
    def detect_vehicles(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect vehicles in the current frame using background subtraction"""
        
        # Apply background subtraction
        fg_mask = self.bg_subtractor.apply(frame)
        
        # Apply morphological operations to clean up the mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by area and extract bounding boxes
        vehicles = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if config.MIN_CONTOUR_AREA <= area <= config.MAX_CONTOUR_AREA:
                x, y, w, h = cv2.boundingRect(contour)
                vehicles.append((x, y, w, h))
        
        return vehicles
    
    def update_trackers(self, vehicle_boxes: List[Tuple[int, int, int, int]]):
        """Update vehicle trackers with new detections"""
        
        # Calculate centers of detected vehicles
        current_centers = []
        for x, y, w, h in vehicle_boxes:
            center_x = x + w // 2
            center_y = y + h // 2
            current_centers.append((center_x, center_y))
        
        # Update existing trackers or create new ones
        used_detections = set()
        
        # Try to match existing trackers with current detections
        for tracker in self.vehicle_trackers:
            best_match_idx = None
            min_distance = float('inf')
            
            last_pos = tracker.get_last_position()
            
            for i, center in enumerate(current_centers):
                if i in used_detections:
                    continue
                
                distance = np.sqrt((center[0] - last_pos[0])**2 + (center[1] - last_pos[1])**2)
                
                if distance < config.MAX_TRACKING_DISTANCE and distance < min_distance:
                    min_distance = distance
                    best_match_idx = i
            
            if best_match_idx is not None:
                tracker.update(current_centers[best_match_idx], self.frame_id)
                used_detections.add(best_match_idx)
        
        # Create new trackers for unmatched detections
        for i, center in enumerate(current_centers):
            if i not in used_detections:
                new_tracker = VehicleTracker(center, self.frame_id)
                self.vehicle_trackers.append(new_tracker)
        
        # Remove old trackers
        self.vehicle_trackers = [
            tracker for tracker in self.vehicle_trackers 
            if self.frame_id - tracker.last_seen < 30  # Remove if not seen for 30 frames
        ]
    
    def count_vehicles(self):
        """Count vehicles that cross the counting line"""
        for tracker in self.vehicle_trackers:
            # Only count vehicles that have been tracked for minimum frames
            if (len(tracker.centers) >= config.MIN_FRAMES_TO_COUNT and 
                tracker.has_crossed_line(self.counting_line_y)):
                
                tracker.counted = True
                self.vehicle_count += 1
                print(f"Vehicle #{self.vehicle_count} counted at frame {self.frame_id}")
    
    def draw_visualizations(self, frame: np.ndarray, vehicle_boxes: List[Tuple[int, int, int, int]]) -> np.ndarray:
        """Draw all visualizations on the frame"""
        
        # Draw counting line
        cv2.line(frame, 
                (0, self.counting_line_y), 
                (self.frame_width, self.counting_line_y),
                config.COUNTING_LINE_COLOR, 
                config.COUNTING_LINE_THICKNESS)
        
        # Draw counting line label
        cv2.putText(frame, "COUNTING LINE", 
                   (10, self.counting_line_y - 10),
                   config.TEXT_FONT, config.TEXT_SCALE, 
                   config.COUNTING_LINE_COLOR, config.TEXT_THICKNESS)
        
        # Draw bounding boxes around detected vehicles
        for x, y, w, h in vehicle_boxes:
            cv2.rectangle(frame, (x, y), (x + w, y + h), 
                         config.BOUNDING_BOX_COLOR, 2)
        
        # Draw tracker centers and paths
        for tracker in self.vehicle_trackers:
            if len(tracker.centers) > 0:
                # Draw center point
                center = tracker.get_last_position()
                cv2.circle(frame, center, 5, config.CENTER_POINT_COLOR, -1)
                
                # Draw tracking path
                if len(tracker.centers) > 1:
                    for i in range(1, len(tracker.centers)):
                        cv2.line(frame, tracker.centers[i-1], tracker.centers[i], 
                               config.CENTER_POINT_COLOR, 2)
        
        # Draw vehicle count
        count_text = f"Vehicles Counted: {self.vehicle_count}"
        cv2.putText(frame, count_text, (10, 30),
                   config.TEXT_FONT, config.TEXT_SCALE, 
                   config.TEXT_COLOR, config.TEXT_THICKNESS)
        
        # Draw FPS
        fps_text = f"FPS: {self.current_fps:.1f}"
        cv2.putText(frame, fps_text, (10, 70),
                   config.TEXT_FONT, config.TEXT_SCALE, 
                   config.TEXT_COLOR, config.TEXT_THICKNESS)
        
        # Draw active trackers count
        trackers_text = f"Active Trackers: {len(self.vehicle_trackers)}"
        cv2.putText(frame, trackers_text, (10, 110),
                   config.TEXT_FONT, config.TEXT_SCALE, 
                   config.TEXT_COLOR, config.TEXT_THICKNESS)
        
        return frame
    
    def calculate_fps(self):
        """Calculate and update FPS"""
        self.fps_counter += 1
        if self.fps_counter % 30 == 0:  # Update FPS every 30 frames
            elapsed_time = time.time() - self.fps_start_time
            self.current_fps = 30 / elapsed_time
            self.fps_start_time = time.time()
    
    def run(self) -> Dict[str, any]:
        """Main processing loop"""
        
        # Initialize video source
        if not self.initialize_video_source():
            return {"success": False, "error": "Failed to initialize video source"}
        
        # Initialize video writer
        if not self.initialize_video_writer():
            print("Warning: Video output will not be saved")
        
        print("=== Vehicle Counting System Started ===")
        print("Press 'q' to quit, 'r' to reset counter")
        print("Press 's' to save current frame")
        
        try:
            while True:
                # Read frame
                ret, frame = self.cap.read()
                if not ret:
                    print("End of video stream or failed to read frame")
                    break
                
                self.frame_id += 1
                
                # Detect vehicles
                vehicle_boxes = self.detect_vehicles(frame)
                
                # Update trackers
                self.update_trackers(vehicle_boxes)
                
                # Count vehicles
                self.count_vehicles()
                
                # Draw visualizations
                output_frame = self.draw_visualizations(frame, vehicle_boxes)
                
                # Calculate FPS
                self.calculate_fps()
                
                # Save frame to output video
                if self.video_writer is not None:
                    self.video_writer.write(output_frame)
                
                # Display frame
                if config.SHOW_GUI:
                    cv2.imshow('Vehicle Counting System', output_frame)
                    
                    # Handle keyboard input
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        print("Quitting...")
                        break
                    elif key == ord('r'):
                        print("Resetting counter...")
                        self.vehicle_count = 0
                        self.vehicle_trackers = []
                    elif key == ord('s'):
                        timestamp = int(time.time())
                        filename = f"frame_{timestamp}.jpg"
                        cv2.imwrite(filename, output_frame)
                        print(f"Frame saved as {filename}")
                
                # Non-GUI mode: process for a reasonable duration or number of frames
                elif self.frame_id > 1000:  # Process 1000 frames in headless mode
                    break
        
        except KeyboardInterrupt:
            print("\nProcessing interrupted by user")
        
        except Exception as e:
            print(f"Error during processing: {str(e)}")
            return {"success": False, "error": str(e)}
        
        finally:
            self.cleanup()
        
        # Return results
        return {
            "success": True,
            "total_frames_processed": self.frame_id,
            "vehicles_counted": self.vehicle_count,
            "average_fps": self.current_fps,
            "output_saved": config.SAVE_OUTPUT and self.video_writer is not None
        }
    
    def cleanup(self):
        """Clean up resources"""
        print(f"\n=== Processing Complete ===")
        print(f"Total frames processed: {self.frame_id}")
        print(f"Total vehicles counted: {self.vehicle_count}")
        print(f"Average FPS: {self.current_fps:.1f}")
        
        if self.cap is not None:
            self.cap.release()
        
        if self.video_writer is not None:
            self.video_writer.release()
            print(f"Output video saved: {config.OUTPUT_VIDEO_PATH}")
        
        cv2.destroyAllWindows()

def main():
    """Main function to run the vehicle counting system"""
    
    print("Vehicle Counting System")
    print("=" * 50)
    print(f"Video source: {config.VIDEO_SOURCE}")
    print(f"GUI display: {config.SHOW_GUI}")
    print(f"Save output: {config.SAVE_OUTPUT}")
    print(f"Min contour area: {config.MIN_CONTOUR_AREA}")
    print(f"Counting line position: {config.COUNTING_LINE_POSITION * 100}%")
    print("=" * 50)
    
    # Create and run the vehicle counting system
    vcs = VehicleCountingSystem()
    results = vcs.run()
    
    if results["success"]:
        print("\nSystem completed successfully!")
        print(f"Results: {results}")
    else:
        print(f"\nSystem failed: {results['error']}")
    
    return results

if __name__ == "__main__":
    main()
