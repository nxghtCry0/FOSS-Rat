import requests
import os
import base64 # NEW: Import for decoding the fallback key

# --- Configuration ---
UPLOAD_URL = "https://freeimage.host/api/1/upload"
API_KEY_FILE = "imagehost_key.txt"

# NEW: Add your Base64 encoded fallback API key here.
# This is NOT a real key. Replace it with the encoded key you just generated.
FALLBACK_API_KEY_B64 = "NmQyMDdlMDIxOThhODQ3YWE5OGQwYTJhOTAxNDg1YTU="

def load_api_key() -> str:
    """
    MODIFIED: Tries to load the API key from the file, otherwise uses the hardcoded fallback.
    """
    try:
        # Priority 1: Try to load from the external file.
        with open(API_KEY_FILE, 'r') as f:
            key = f.read().strip()
            print("[Uploader] Loaded API key from file.")
            return key
    except FileNotFoundError:
        # Priority 2: If the file doesn't exist, use the fallback.
        print(f"[Uploader] '{API_KEY_FILE}' not found. Using hardcoded fallback key.")
        try:
            # Decode the Base64 string to get the actual key.
            fallback_key = base64.b64decode(FALLBACK_API_KEY_B64).decode('utf-8')
            return fallback_key
        except Exception as e:
            # This will catch errors from invalid Base64 strings.
            print(f"[Uploader] FATAL ERROR: Could not decode the fallback API key. Error: {e}")
            raise
    except Exception as e:
        print(f"[Uploader] FATAL ERROR: An unexpected error occurred while loading the API key: {e}")
        raise

def upload_image(image_bytes: bytes) -> str | None:
    """
    Uploads image bytes to freeimage.host and returns the direct image URL.
    
    Args:
        image_bytes: The raw bytes of the image (e.g., a JPEG or PNG).
        
    Returns:
        The direct URL to the uploaded image, or None on failure.
    """
    try:
        # This function now seamlessly uses whichever key is available.
        api_key = load_api_key()
        
        params = {'key': api_key}
        files = {'source': ('capture.jpg', image_bytes, 'image/jpeg')}
        
        response = requests.post(UPLOAD_URL, params=params, files=files, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("status_code") == 200:
            return data.get("image", {}).get("url")
        else:
            print(f"[Uploader] API returned an error: {data.get('status_txt')}")

    except FileNotFoundError as e:
        # This will now only trigger if both the file is missing AND the fallback is broken.
        print(f"[Uploader] FATAL: {e}")
    except requests.exceptions.RequestException as e:
        print(f"[Uploader] Network error during image upload: {e}")
    except Exception as e:
        print(f"[Uploader] A general error occurred during image upload: {e}")
        
    return None