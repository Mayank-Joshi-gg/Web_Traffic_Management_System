import psutil


def get_resources():
    """Return host CPU, memory and process metrics."""
    return {
        "cpu": psutil.cpu_percent(interval=0.1),
        "memory": psutil.virtual_memory().percent,
        "processes": len(psutil.pids())
    }


if __name__ == "__main__":
    metrics = get_resources()
    print(f"CPU: {metrics['cpu']}%")
    print(f"Memory: {metrics['memory']}%")
    print(f"Processes: {metrics['processes']}")
