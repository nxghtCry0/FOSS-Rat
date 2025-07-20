import discord
from discord.ext import commands
import os

# Import all your custom modules
import command_executor as cmd
import notification_sender as notifier
import screenshot_taker as ss
import system_info as sysinfo
import web_opener

TOKEN_PATH = 'token.txt'
AUTHORIZED_USERS = [1153459521251983470]

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

def load_token() -> str:
    if not os.path.exists(TOKEN_PATH):
        raise FileNotFoundError(f"Token file not found: {TOKEN_PATH}")
    with open(TOKEN_PATH, 'r') as f:
        return f.read().strip()

# --- Existing Commands (runcmd, shownotification, takescreenshot) ---
# (No changes needed to your previous commands)
@bot.tree.command(name="runcmd", description="Execute system command (Owner only)")
async def runcmd(interaction: discord.Interaction, command: str):
    if interaction.user.id not in AUTHORIZED_USERS:
        return await interaction.response.send_message("⛔ Unauthorized access attempted!", ephemeral=True)
    await interaction.response.defer()
    output = cmd.execute_command(command)
    if len(output) > 1900:
        output = output[:1900] + "\n[...TRUNCATED...]"
    await interaction.followup.send(f"```\n📟 COMMAND: {command}\n💻 OUTPUT:\n{output}\n```")

@bot.tree.command(name="shownotification", description="Displays a desktop notification (Owner only)")
async def shownotification(interaction: discord.Interaction, title: str, message: str):
    if interaction.user.id not in AUTHORIZED_USERS:
        return await interaction.response.send_message("⛔ Unauthorized access attempted!", ephemeral=True)
    success = notifier.show(title, message)
    if success:
        await interaction.response.send_message(f"✅ Notification sent: **{title}**", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Failed to send notification. Check console.", ephemeral=True)

@bot.tree.command(name="takescreenshot", description="Takes a screenshot of the host machine (Owner only)")
async def takescreenshot(interaction: discord.Interaction):
    if interaction.user.id not in AUTHORIZED_USERS:
        return await interaction.response.send_message("⛔ Unauthorized access attempted!", ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    screenshot_file = ss.take_screenshot()
    if screenshot_file and os.path.exists(screenshot_file):
        try:
            await interaction.followup.send(file=discord.File(screenshot_file))
        finally:
            os.remove(screenshot_file)
    else:
        await interaction.followup.send("❌ Failed to take screenshot. Check console for errors.", ephemeral=True)

# --- New Commands ---

@bot.tree.command(name="systemspecs", description="Shows hardware specs of the host machine (Owner only)")
async def systemspecs(interaction: discord.Interaction):
    if interaction.user.id not in AUTHORIZED_USERS:
        return await interaction.response.send_message("⛔ Unauthorized access attempted!", ephemeral=True)
        
    await interaction.response.defer()
    
    specs = sysinfo.get_specs()
    
    embed = discord.Embed(title="💻 System Specifications", color=discord.Color.blue())
    embed.add_field(name="Operating System", value=f"{specs['platform']} {specs['platform_release']}", inline=False)
    embed.add_field(name="CPU", value=f"{specs['cpu_name']}", inline=False)
    embed.add_field(name="CPU Usage", value=f"{specs['cpu_usage']}%", inline=True)
    embed.add_field(name="Cores", value=f"{specs['cpu_physical_cores']} Physical, {specs['cpu_total_cores']} Total", inline=True)
    embed.add_field(name="RAM Usage", value=f"{specs['ram_usage_percent']}% ({specs['ram_available']} free of {specs['ram_total']})", inline=False)
    
    for i, gpu in enumerate(specs['gpus']):
        gpu_name = f"GPU {i}: {gpu['name']}"
        gpu_stats = (f"Load: {gpu.get('load', 'N/A')} | "
                     f"Temp: {gpu.get('temperature', 'N/A')} | "
                     f"VRAM: {gpu.get('vram_used', 'N/A')} / {gpu.get('vram_total', 'N/A')}")
        embed.add_field(name=gpu_name, value=gpu_stats, inline=False)

    await interaction.followup.send(embed=embed)


@bot.tree.command(name="openwebsite", description="Opens a URL on the host machine (Owner only)")
async def openwebsite(interaction: discord.Interaction, url: str):
    if interaction.user.id not in AUTHORIZED_USERS:
        return await interaction.response.send_message("⛔ Unauthorized access attempted!", ephemeral=True)
    
    success = web_opener.open_url(url)
    
    if success:
        await interaction.response.send_message(f"✅ Attempted to open `{url}` on the host machine.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Failed to open URL. Check console for details.", ephemeral=True)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)
    print('------')

if __name__ == "__main__":
    bot.run(load_token())