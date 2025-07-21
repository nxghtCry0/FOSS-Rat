import requests

def download_from_url(url: str, save_path: str) -> str:
    """
    Downloads a file from a direct URL and saves it to a specified path.

    Args:
        url: The direct download link to the file.
        save_path: The full path (including filename) to save the file on the local machine.

    Returns:
        A status message indicating success or failure.
    """
    try:
        # Use a stream to handle potentially large files without loading them all into memory.
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
            with open(save_path, 'wb') as f:
                # Write the file to disk in chunks.
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return f"✅ Successfully downloaded file from URL and saved to `{save_path}`."
    except requests.exceptions.RequestException as e:
        return f"❌ Failed to download file from URL. Error: {e}"
    except Exception as e:
        return f"❌ An unexpected error occurred during URL download: {e}"