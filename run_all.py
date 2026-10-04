import subprocess
import sys

servers = [
    "servers/server1.py",
    "servers/server2.py",
    "servers/server3.py"
]

processes = []

try:

    for server in servers:
        process = subprocess.Popen(
            [sys.executable, server]
        )

        processes.append(process)

    print("All servers are running.")
    print("Server 1 → http://127.0.0.1:5001")
    print("Server 2 → http://127.0.0.1:5002")
    print("Server 3 → http://127.0.0.1:5003")

    print("\nPress CTRL+C to stop.")

    for process in processes:
        process.wait()

except KeyboardInterrupt:

    print("\nStopping servers...")

    for process in processes:
        process.terminate()