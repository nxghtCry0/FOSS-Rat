import discord
import os
import platform
from typing import Dict

# This dictionary stores the current path for each channel's explorer session.
# Format: { channel_id: "C:\\Users\\..." }
explorer_sessions: Dict[int, str] = {}

class DirectoryChangeModal(discord.ui.Modal, title="Change Directory"):
    """A pop-up modal to get directory input from the user."""
    
    directory_input = discord.ui.TextInput(
        label="Enter Directory Name or Number",
        placeholder="e.g., 'Users' or '1'",
        style=discord.TextStyle.short,
        required=True
    )

    def __init__(self, current_dirs: list):
        super().__init__()
        self.current_dirs = current_dirs
        self.target_dir = None

    async def on_submit(self, interaction: discord.Interaction):
        input_val = self.directory_input.value.strip()

        if input_val.isdigit():
            dir_index = int(input_val) - 1
            if 0 <= dir_index < len(self.current_dirs):
                self.target_dir = self.current_dirs[dir_index]
            else:
                return await interaction.response.send_message("⛔ Invalid directory number.", ephemeral=True)
        else:
            # Case-insensitive search for directory name
            found = next((d for d in self.current_dirs if d.lower() == input_val.lower()), None)
            if found:
                self.target_dir = found
            else:
                return await interaction.response.send_message(f"⛔ Directory '{input_val}' not found.", ephemeral=True)

        await interaction.response.defer()

class FileExplorerView(discord.ui.View):
    """A persistent view with buttons to control the file explorer."""
    
    def __init__(self):
        super().__init__(timeout=None) # Set timeout to None for persistence

    async def update_view(self, interaction: discord.Interaction, new_path: str):
        """Updates the explorer message with the content of the new path."""
        channel_id = interaction.channel.id
        explorer_sessions[channel_id] = new_path
        
        embed, dirs = create_explorer_embed(new_path)
        
        # Pass the new list of directories to the modal
        self.children[3].callback = self.create_modal_callback(dirs)
        
        await interaction.message.edit(embed=embed, view=self)

    @discord.ui.button(label="⬆️ Up", style=discord.ButtonStyle.primary, custom_id="fe_up")
    async def up_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel_id = interaction.channel.id
        current_path = explorer_sessions.get(channel_id, os.path.abspath(os.sep))
        
        new_path = os.path.dirname(current_path)
        if new_path == current_path: # Already at root
            return await interaction.response.send_message("Already at the root directory.", ephemeral=True)
        
        await interaction.response.defer()
        await self.update_view(interaction, new_path)

    @discord.ui.button(label="🏠 Root", style=discord.ButtonStyle.success, custom_id="fe_root")
    async def root_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        new_path = os.path.abspath(os.sep)
        await interaction.response.defer()
        await self.update_view(interaction, new_path)

    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary, custom_id="fe_refresh")
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel_id = interaction.channel.id
        current_path = explorer_sessions.get(channel_id, os.path.abspath(os.sep))
        await interaction.response.defer()
        await self.update_view(interaction, current_path)
        
    @discord.ui.button(label="📂 Change Directory", style=discord.ButtonStyle.danger, custom_id="fe_change_dir")
    async def change_dir_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # This callback is dynamically generated to get current directory context
        pass
        
    def create_modal_callback(self, current_dirs: list):
        """Factory to create a callback for the change directory button."""
        async def modal_callback(interaction: discord.Interaction):
            modal = DirectoryChangeModal(current_dirs)
            await interaction.response.send_modal(modal)
            await modal.wait()
            
            if modal.target_dir:
                channel_id = interaction.channel.id
                current_path = explorer_sessions.get(channel_id, os.path.abspath(os.sep))
                new_path = os.path.join(current_path, modal.target_dir)
                await self.update_view(interaction, new_path)
        return modal_callback

def create_explorer_embed(path: str):
    """Creates the Discord embed for the file explorer UI."""
    embed = discord.Embed(title="File Explorer", description=f"**Current Path:** `{path}`", color=discord.Color.orange())
    dirs, files = [], []

    try:
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_dir():
                    dirs.append(entry.name)
                else:
                    files.append(entry.name)
        dirs.sort(key=str.lower)
        files.sort(key=str.lower)

        dir_list_str = "\n".join(f"**{i+1}.** 📁 `{d}`" for i, d in enumerate(dirs)) or "No directories."
        if len(dir_list_str) > 1024: dir_list_str = dir_list_str[:1020] + "\n..."
        embed.add_field(name="Directories", value=dir_list_str, inline=False)

        file_list_str = "\n".join(f"📄 `{f}`" for f in files) or "No files."
        if len(file_list_str) > 1024: file_list_str = file_list_str[:1020] + "\n..."
        embed.add_field(name="Files", value=file_list_str, inline=False)

    except PermissionError:
        embed.add_field(name="Error", value="⛔ **Permission Denied**", inline=False)
    except FileNotFoundError:
        embed.add_field(name="Error", value="❌ **Directory Not Found**", inline=False)
    except Exception as e:
        embed.add_field(name="Error", value=f"An unexpected error occurred: {e}", inline=False)
        
    embed.set_footer(text="Use buttons to navigate. Directory names are case-insensitive.")
    return embed, dirs