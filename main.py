import discord
from discord.ext import commands
import os
import command_executor as cmd  # Updated import

TOKEN_PATH = 'token.txt'
AUTHORIZED_USERS = [123456789012345678]  # Your User ID

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

@bot.slash_command(name="runcmd", description="Execute system command (Owner only)")
async def runcmd(
    ctx: discord.ApplicationContext,
    command: str = discord.Option(description="Command to execute")  # Fixed syntax
):
    if ctx.author.id not in AUTHORIZED_USERS:
        await ctx.respond("⛔ Unauthorized access attempted!")
        return
    
    await ctx.defer()
    output = cmd.execute_command(command)
    
    if len(output) > 1900:
        output = output[:1900] + "\n[...TRUNCATED...]"
    
    await ctx.followup.send(f"```\n📟 COMMAND: {command}\n💻 OUTPUT:\n{output}\n```")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

if __name__ == "__main__":
    bot.run(load_token())