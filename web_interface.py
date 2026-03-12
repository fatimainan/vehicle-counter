"""
Web interface for the Vehicle Counting System
Provides a simple web-based control panel and results display
"""

from flask import Flask, render_template, jsonify, request
import threading
import time
import os
import json
from vehicle_counter import VehicleCountingSystem
import config

app = Flask(__name__)

# Global variables to store system state
system_instance = None
system_thread = None
system_results = {"status": "idle", "data": {}}
system_running = False

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get current system status"""
    global system_results, system_running
    
    # Add runtime information
    status_data = {
        "running": system_running,
        "results": system_results,
        "config": {
            "video_source": config.VIDEO_SOURCE,
            "show_gui": config.SHOW_GUI,
            "save_output": config.SAVE_OUTPUT,
            "min_contour_area": config.MIN_CONTOUR_AREA,
            "counting_line_position": config.COUNTING_LINE_POSITION
        }
    }
    
    return jsonify(status_data)

@app.route('/api/start', methods=['POST'])
def start_system():
    """Start the vehicle counting system"""
    global system_instance, system_thread, system_running
    
    if system_running:
        return jsonify({"success": False, "message": "System is already running"})
    
    try:
        # Get configuration from request if provided
        request_data = request.get_json() or {}
        
        # Update config if parameters provided
        if 'video_source' in request_data:
            config.VIDEO_SOURCE = request_data['video_source']
        if 'show_gui' in request_data:
            config.SHOW_GUI = request_data['show_gui']
        if 'save_output' in request_data:
            config.SAVE_OUTPUT = request_data['save_output']
        if 'min_contour_area' in request_data:
            config.MIN_CONTOUR_AREA = request_data['min_contour_area']
        
        # Create system instance
        system_instance = VehicleCountingSystem()
        
        # Start system in separate thread
        def run_system():
            global system_results, system_running
            system_running = True
            system_results = {"status": "running", "data": {}}
            
            try:
                results = system_instance.run()
                system_results = {"status": "completed", "data": results}
            except Exception as e:
                system_results = {"status": "error", "data": {"error": str(e)}}
            finally:
                system_running = False
        
        system_thread = threading.Thread(target=run_system)
        system_thread.daemon = True
        system_thread.start()
        
        return jsonify({"success": True, "message": "System started successfully"})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to start system: {str(e)}"})

@app.route('/api/stop', methods=['POST'])
def stop_system():
    """Stop the vehicle counting system"""
    global system_running, system_instance
    
    if not system_running:
        return jsonify({"success": False, "message": "System is not running"})
    
    try:
        # Set running flag to False
        system_running = False
        
        # If system instance exists, trigger cleanup
        if system_instance:
            # Note: In a real implementation, you might want to implement
            # a more graceful shutdown mechanism
            pass
        
        return jsonify({"success": True, "message": "Stop signal sent"})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to stop system: {str(e)}"})

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    """Get or update system configuration"""
    
    if request.method == 'GET':
        # Return current configuration
        current_config = {
            "video_source": config.VIDEO_SOURCE,
            "fallback_video": config.FALLBACK_VIDEO,
            "show_gui": config.SHOW_GUI,
            "save_output": config.SAVE_OUTPUT,
            "output_video_path": config.OUTPUT_VIDEO_PATH,
            "min_contour_area": config.MIN_CONTOUR_AREA,
            "max_contour_area": config.MAX_CONTOUR_AREA,
            "counting_line_position": config.COUNTING_LINE_POSITION,
            "background_history": config.BACKGROUND_HISTORY,
            "background_threshold": config.BACKGROUND_THRESHOLD
        }
        return jsonify(current_config)
    
    elif request.method == 'POST':
        # Update configuration
        if system_running:
            return jsonify({"success": False, "message": "Cannot update config while system is running"})
        
        try:
            new_config = request.get_json()
            
            # Update configuration values
            if 'video_source' in new_config:
                config.VIDEO_SOURCE = new_config['video_source']
            if 'show_gui' in new_config:
                config.SHOW_GUI = new_config['show_gui']
            if 'save_output' in new_config:
                config.SAVE_OUTPUT = new_config['save_output']
            if 'min_contour_area' in new_config:
                config.MIN_CONTOUR_AREA = new_config['min_contour_area']
            if 'max_contour_area' in new_config:
                config.MAX_CONTOUR_AREA = new_config['max_contour_area']
            if 'counting_line_position' in new_config:
                config.COUNTING_LINE_POSITION = new_config['counting_line_position']
            if 'background_history' in new_config:
                config.BACKGROUND_HISTORY = new_config['background_history']
            if 'background_threshold' in new_config:
                config.BACKGROUND_THRESHOLD = new_config['background_threshold']
            
            return jsonify({"success": True, "message": "Configuration updated successfully"})
            
        except Exception as e:
            return jsonify({"success": False, "message": f"Failed to update config: {str(e)}"})

@app.route('/api/files')
def list_files():
    """List available video files and outputs"""
    try:
        files = {
            "video_files": [],
            "output_files": [],
            "log_files": []
        }
        
        # Get current directory files
        current_dir = "."
        for filename in os.listdir(current_dir):
            if filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                file_info = {
                    "name": filename,
                    "size": os.path.getsize(filename),
                    "modified": os.path.getmtime(filename)
                }
                
                if filename.startswith('output'):
                    files["output_files"].append(file_info)
                else:
                    files["video_files"].append(file_info)
            elif filename.endswith('.log'):
                files["log_files"].append({
                    "name": filename,
                    "size": os.path.getsize(filename),
                    "modified": os.path.getmtime(filename)
                })
        
        return jsonify(files)
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to list files: {str(e)}"})

if __name__ == '__main__':
    print("Starting Vehicle Counting System Web Interface...")
    print("Access the interface at: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
