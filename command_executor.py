import subprocess
import os

def execute_command(command: str) -> str:
    """Executes a standard command prompt (cmd.exe) command."""
    if not command:
        return "No command provided."
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
            check=False
        )
        output = result.stdout + result.stderr
        if not output:
            return "Command executed but produced no output."
        return output
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 2 minutes."
    except Exception as e:
        return f"An error occurred while executing the command: {e}"

def execute_powershell(command: str) -> str:
    """Executes a PowerShell command."""
    if not command:
        return "No PowerShell command provided."
    try:
        full_command = f"powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \"{command}\""
        result = subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
            check=False
        )
        output = result.stdout + result.stderr
        if not output:
            return "PowerShell command executed but produced no output."
        return output
    except subprocess.TimeoutExpired:
        return "Error: PowerShell command timed out after 2 minutes."
    except Exception as e:
        return f"An error occurred while executing the PowerShell command: {e}"