import mss
import mss.tools
from datetime import datetime

def take_screenshot() -> str:
    """
    Captures a screenshot of the primary monitor.

    Returns:
        str: The file path of the saved screenshot.
    """
    try:
        with mss.mss() as sct:
            # Generate a unique filename with a timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"screenshot_{timestamp}.png"
            
            # Grab the data
            sct.shot(output=filename)
            
            return filename
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        return None