import os
import time

def get_system_uptime() -> dict:
    """
    Returns the system uptime in a human-readable format.
    Returns:
        A dictionary with the uptime string.
    """
    try:
        if os.path.exists("/proc/uptime"):
            with open("/proc/uptime", "r") as f:
                uptime_seconds = float(f.readline().split()[0])
        else:
            try:
                import psutil
                uptime_seconds = time.time() - psutil.boot_time()
            except ImportError:
                return {"result": "Uptime not available (psutil not installed and /proc/uptime missing)."}
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)
        parts = []
        if days: parts.append(f"{days}d")
        if hours: parts.append(f"{hours}h")
        if minutes: parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        return {"result": f"System uptime: {' '.join(parts)}"}
    except Exception as e:
        return {"result": f"Failed to get uptime: {e}"}
