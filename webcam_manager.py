import cv2
import os
import time

def capture_webcam_image() -> (str | None):
    """
    Captures a single high-quality image from the default webcam.

    Returns:
        str: The file path of the saved image if successful.
        None: If no webcam is found or an error occurs.
    """
    # Use 0 for the default webcam. Change if you have multiple cameras.
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return None

    try:
        # Give the camera a moment to adjust to lighting
        time.sleep(1) 

        # Read a few frames to allow the camera's auto-exposure to settle
        for _ in range(5):
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture frame during warm-up.")
                return None
        
        # Capture the final, stable frame
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame from webcam.")
            return None

        # Define a temporary file path. Using the system's temp directory is best practice.
        temp_dir = os.getenv("TEMP", ".") # Fallback to current dir if TEMP env var not found
        file_path = os.path.join(temp_dir, f"webcam_capture_{int(time.time())}.png")
        
        # Save the captured frame to the file
        cv2.imwrite(file_path, frame)
        
        print(f"Webcam image saved to {file_path}")
        return file_path

    finally:
        # CRITICAL: Always release the camera.
        # This turns off the webcam and the indicator light.
        cap.release()