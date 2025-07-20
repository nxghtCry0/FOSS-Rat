import psutil
import GPUtil
import platform

def get_specs() -> dict:
    """
    Gathers detailed system specifications including CPU, RAM, and GPU(s).

    Returns:
        dict: A dictionary containing system information.
    """
    specs = {}
    
    # OS Info
    specs['platform'] = platform.system()
    specs['platform_release'] = platform.release()
    specs['platform_version'] = platform.version()
    specs['architecture'] = platform.machine()
    
    # CPU Info
    specs['cpu_name'] = platform.processor()
    specs['cpu_physical_cores'] = psutil.cpu_count(logical=False)
    specs['cpu_total_cores'] = psutil.cpu_count(logical=True)
    specs['cpu_usage'] = psutil.cpu_percent(interval=1)
    
    # RAM Info
    ram = psutil.virtual_memory()
    specs['ram_total'] = f"{ram.total / (1024**3):.2f} GB"
    specs['ram_available'] = f"{ram.available / (1024**3):.2f} GB"
    specs['ram_usage_percent'] = ram.percent
    
    # GPU Info
    try:
        gpus = GPUtil.getGPUs()
        specs['gpus'] = []
        if gpus:
            for gpu in gpus:
                specs['gpus'].append({
                    'name': gpu.name,
                    'load': f"{gpu.load*100:.2f}%",
                    'vram_free': f"{gpu.memoryFree}MB",
                    'vram_used': f"{gpu.memoryUsed}MB",
                    'vram_total': f"{gpu.memoryTotal}MB",
                    'temperature': f"{gpu.temperature} °C"
                })
        else:
            specs['gpus'].append({'name': "No NVIDIA/AMD GPU detected by GPUtil"})
    except Exception as e:
        specs['gpus'] = [{'name': f"GPU check failed: {e}"}]
        
    return specs