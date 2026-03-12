"""
Main entry point for the Vehicle Counting System
This file provides multiple ways to run the system:
1. Direct OpenCV processing (command line)
2. Web interface (browser-based control)
"""

import sys
import os
import argparse
from vehicle_counter import main as run_vehicle_counter
from web_interface import app
import config

def print_banner():
    """Print system banner"""
    print("=" * 60)
    print("🚗 VEHICLE COUNTING SYSTEM")
    print("Real-time Vehicle Detection and Counting using OpenCV")
    print("=" * 60)
    print()

def print_usage():
    """Print usage instructions"""
    print("Usage Options:")
    print("1. Direct OpenCV Processing:")
    print("   python main.py --mode direct")
    print("   python main.py --mode direct --no-gui --save-output")
    print()
    print("2. Web Interface (Recommended):")
    print("   python main.py --mode web")
    print("   Then open: http://localhost:5000")
    print()
    print("3. Configuration Options:")
    print("   --video-source 0           # Use webcam")
    print("   --video-source traffic.mp4 # Use video file")
    print("   --no-gui                   # Disable GUI display")
    print("   --save-output              # Save output video")
    print("   --min-area 1000            # Minimum detection area")
    print()

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Vehicle Counting System using OpenCV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --mode web
  python main.py --mode direct --video-source 0 --save-output
  python main.py --mode direct --video-source traffic.mp4 --no-gui
        """
    )
    
    parser.add_argument(
        '--mode', 
        choices=['direct', 'web'], 
        default='web',
        help='Execution mode: direct (OpenCV) or web (browser interface)'
    )
    
    parser.add_argument(
        '--video-source',
        default=config.VIDEO_SOURCE,
        help='Video source: 0 for webcam or path to video file'
    )
    
    parser.add_argument(
        '--no-gui',
        action='store_true',
        help='Disable GUI display (headless mode)'
    )
    
    parser.add_argument(
        '--save-output',
        action='store_true',
        help='Save output video to file'
    )
    
    parser.add_argument(
        '--min-area',
        type=int,
        default=config.MIN_CONTOUR_AREA,
        help='Minimum contour area for vehicle detection'
    )
    
    parser.add_argument(
        '--counting-line',
        type=float,
        default=config.COUNTING_LINE_POSITION,
        help='Counting line position (0.0 to 1.0 from top)'
    )
    
    parser.add_argument(
        '--output-path',
        default=config.OUTPUT_VIDEO_PATH,
        help='Output video file path'
    )
    
    return parser.parse_args()

def update_config_from_args(args):
    """Update configuration based on command line arguments"""
    
    # Handle video source (convert to int if it's a digit)
    if isinstance(args.video_source, str) and args.video_source.isdigit():
        config.VIDEO_SOURCE = int(args.video_source)
    else:
        config.VIDEO_SOURCE = args.video_source
    
    # Update other configuration
    if args.no_gui:
        config.SHOW_GUI = False
    
    if args.save_output:
        config.SAVE_OUTPUT = True
    
    config.MIN_CONTOUR_AREA = args.min_area
    config.COUNTING_LINE_POSITION = args.counting_line
    config.OUTPUT_VIDEO_PATH = args.output_path

def run_direct_mode():
    """Run the system in direct OpenCV mode"""
    print("🎯 Starting Direct OpenCV Mode")
    print("-" * 40)
    print(f"Video Source: {config.VIDEO_SOURCE}")
    print(f"GUI Display: {config.SHOW_GUI}")
    print(f"Save Output: {config.SAVE_OUTPUT}")
    print(f"Min Detection Area: {config.MIN_CONTOUR_AREA}")
    print(f"Counting Line: {config.COUNTING_LINE_POSITION * 100}%")
    print("-" * 40)
    print()
    
    # Run the vehicle counter
    results = run_vehicle_counter()
    
    # Print results
    print()
    print("📊 FINAL RESULTS")
    print("-" * 40)
    if results.get("success"):
        print(f"✅ Processing completed successfully!")
        print(f"🚗 Vehicles counted: {results.get('vehicles_counted', 0)}")
        print(f"🎬 Frames processed: {results.get('total_frames_processed', 0)}")
        print(f"⚡ Average FPS: {results.get('average_fps', 0):.1f}")
        if results.get('output_saved'):
            print(f"💾 Output saved: {config.OUTPUT_VIDEO_PATH}")
    else:
        print(f"❌ Processing failed: {results.get('error', 'Unknown error')}")
    print("-" * 40)

def run_web_mode():
    """Run the system in web interface mode"""
    print("🌐 Starting Web Interface Mode")
    print("-" * 40)
    print("📱 Access the web interface at:")
    print("   http://localhost:5000")
    print("   http://0.0.0.0:5000")
    print()
    print("🎛️  Web interface features:")
    print("   - Real-time system control")
    print("   - Configuration management")
    print("   - Live status monitoring")
    print("   - System logs and results")
    print()
    print("⏹️  Press Ctrl+C to stop the web server")
    print("-" * 40)
    print()
    
    # Start the web application
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Web server stopped by user")

def check_dependencies():
    """Check if required dependencies are available"""
    try:
        import cv2
        import numpy as np
        from flask import Flask
        print("✅ All dependencies available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Please install required packages:")
        print("   pip install opencv-python numpy flask")
        return False

def main():
    """Main entry point"""
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Show usage if no specific mode
    if len(sys.argv) == 1:
        print_usage()
        print("🚀 Starting in default web mode...")
        print("   Use --mode direct for command-line processing")
        print()
    
    # Update configuration based on arguments
    update_config_from_args(args)
    
    # Run in selected mode
    try:
        if args.mode == 'direct':
            run_direct_mode()
        elif args.mode == 'web':
            run_web_mode()
        else:
            print(f"❌ Unknown mode: {args.mode}")
            print_usage()
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Processing interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
