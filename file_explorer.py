import discord
import os

def format_size(size_bytes):
    """Converts bytes into a human-readable format (KB, MB, GB)."""
    if size_bytes == 0: return "0B"
    import math
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def create_explorer_embed(path: str) -> discord.Embed:
    """
    Creates a Discord embed showing the contents and file sizes of a directory.
    """
    if not path: path = '.'
    abs_path = os.path.abspath(path)
    
    embed = discord.Embed(title="File Explorer", description=f"**Listing for:** `{abs_path}`", color=discord.Color.orange())
    dirs, files = [], []

    try:
        with os.scandir(abs_path) as it:
            for entry in it:
                if entry.is_dir():
                    dirs.append(entry.name)
                else:
                    try:
                        size = entry.stat().st_size
                        files.append((entry.name, size))
                    except FileNotFoundError:
                        continue
        dirs.sort(key=str.lower)
        files.sort(key=lambda x: str.lower(x[0]))

        dir_list_str = "\n".join(f"📁 `{d}`" for d in dirs) or "No sub-directories found."
        embed.add_field(name="Directories", value=dir_list_str, inline=False)

        file_list_str = "\n".join(f"📄 `{f}` - `{format_size(s)}`" for f, s in files) or "No files found."
        if len(file_list_str) > 1024: file_list_str = file_list_str[:1020] + "\n..."
        embed.add_field(name="Files", value=file_list_str, inline=False)
        
        embed.set_footer(text="Use ?download <file_path> to retrieve a file.")

    except Exception as e:
        embed.clear_fields()
        embed.add_field(name="Error", value=f"⛔ **An error occurred:**\n{e}", inline=False)
        
    return embed