from flask import Flask, jsonify
import sys
import time
import threading

app = Flask(__name__)

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5001
SERVER_ID = PORT - 5000

active_requests = 0
lock = threading.Lock()


@app.route("/")
def home():
    global active_requests

    with lock:
        active_requests += 1

    start = time.time()

    # Small delay to make response-time comparison visible.
    time.sleep(0.05)

    response = {
        "server_id": SERVER_ID,
        "server_port": PORT,
        "message": "Request handled successfully",
        "active_requests": active_requests
    }

    with lock:
        active_requests -= 1

    response["response_time"] = round(time.time() - start, 4)
    return jsonify(response)


@app.route("/status")
def status():
    with lock:
        current = active_requests

    return jsonify({
        "server_id": SERVER_ID,
        "port": PORT,
        "active_requests": current,
        "status": "UP"
    })


if __name__ == "__main__":
    print(f"Starting Server {SERVER_ID} on port {PORT}")
    app.run(port=PORT, debug=False, threaded=True)
