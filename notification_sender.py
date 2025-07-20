from plyer import notification

def show(title: str, message: str):
    """
    Displays a desktop notification on the host machine.
    
    Args:
        title (str): The title of the notification.
        message (str): The main message content of the notification.
    """
    try:
        notification.notify(
            title=title,
            message=message,
            app_name='Discord Bot',  # You can customize this
            timeout=10  # Notification will disappear after 10 seconds
        )
        print(f"Notification Sent: '{title}'")
        return True
    except Exception as e:
        # This will print the error to your console if plyer fails
        print(f"Error showing notification: {e}")
        return False