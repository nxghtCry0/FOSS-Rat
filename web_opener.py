import webbrowser

def open_url(url: str) -> bool:
    """
    Opens a URL in the default web browser on the host machine.

    Args:
        url (str): The URL to open.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Prepend http:// if no scheme is present
        if not (url.startswith('http://') or url.startswith('https://')):
            url = 'http://' + url
            
        webbrowser.open(url, new=2) # new=2 opens in a new tab, if possible
        print(f"Opened URL: {url}")
        return True
    except Exception as e:
        print(f"Error opening URL {url}: {e}")
        return False