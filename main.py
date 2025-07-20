import discord
from discord.ext import commands
import os
import command_executor as cmd
import notification_sender as notifier # 1. Import the new module

TOKEN_PATH = 'token.txt'
AUTHORIZED_USERS = [1153459521251983470]  # Your User ID

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix='!',
    intents=intents,
    help_command=None
)

def load_token() -> str:
    if not os.path.exists(TOKEN_PATH):
        raise FileNotFoundError(f"Token file not found: {TOKEN_PATH}")
    with open(TOKEN_PATH, 'r') as f:
        return f.read().strip()

@bot.tree.command(name="runcmd", description="Execute system command (Owner only)")
async def runcmd(
    interaction: discord.Interaction,
    command: str
):
    if interaction.user.id not in AUTHORIZED_USERS:
        await interaction.response.send_message("⛔ Unauthorized access attempted!", ephemeral=True)
        return
    
    await interaction.response.defer()
    output = cmd.execute_command(command)
    
    if len(output) > 1900:
        output = output[:1900] + "\n[...TRUNCATED...]"
    
    await interaction.followup.send(f"```\n📟 COMMAND: {command}\n💻 OUTPUT:\n{output}\n```")

# 2. Add the new slash command for notifications
@bot.tree.command(name="shownotification", description="Displays a desktop notification (Owner only)")
async def shownotification(
    interaction: discord.Interaction,
    title: str,
    message: str
):
    """Sends a notification to the computer running the bot."""
    if interaction.user.id not in AUTHORIZED_USERS:
        await interaction.response.send_message("⛔ Unauthorized access attempted!", ephemeral=True)
        return
        
    # Call the function from our new module
    success = notifier.show(title, message)
    
    if success:
        # Send a confirmation message back to Discord
        await interaction.response.send_message(f"✅ Notification sent: **{title}**", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Failed to send notification. Check console.", ephemeral=True)


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