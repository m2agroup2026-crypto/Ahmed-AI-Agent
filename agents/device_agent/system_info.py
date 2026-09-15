import platform
import os
import sys


def get_system_info():
    return {
        "device_name": platform.node(),
        "operating_system": platform.system(),
        "os_version": platform.version(),
        "processor": platform.processor(),
        "python_version": sys.version.split()[0],
        "cpu_count": os.cpu_count(),
    }


def print_system_info():
    info = get_system_info()

    print("\n=== Ahmed AI Device Report ===\n")

    for key, value in info.items():
        print(f"{key}: {value}")
