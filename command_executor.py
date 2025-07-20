import subprocess

def execute_command(command: str) -> str:
    try:
        result = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
            encoding='utf-8',
            errors='replace'
        )
        output = result.stdout + result.stderr
        return output if output else "Command executed (no output)"
    
    except subprocess.TimeoutExpired:
        return "Error: Command timed out (30s limit)"
    except Exception as e:
        return f"Error: {str(e)}"