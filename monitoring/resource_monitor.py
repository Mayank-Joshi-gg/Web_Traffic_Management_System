import psutil


def get_resources():
    return {
        "cpu": psutil.cpu_percent(interval=0.2),
        "memory": psutil.virtual_memory().percent,
        "processes": len(psutil.pids())
    }


if __name__ == "__main__":
    data = get_resources()
    print("CPU:", data["cpu"], "%")
    print("Memory:", data["memory"], "%")
    print("Processes:", data["processes"])
