import sys
import time
import threading
from flask import Flask, jsonify, request
from monitoring.resource_monitor import get_resources

app = Flask(__name__)
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5001
SERVER_ID = PORT - 5000
active_requests = 0
request_lock = threading.Lock()


def begin_request():
    global active_requests
    with request_lock:
        active_requests += 1


def end_request():
    global active_requests
    with request_lock:
        active_requests = max(0, active_requests - 1)


@app.route("/", methods=["GET"])
def home():
    begin_request()
    started = time.monotonic()
    try:
        # Small workload to make request distribution measurable.
        time.sleep(0.05)
        return jsonify({
            "server_id": SERVER_ID,
            "server_port": PORT,
            "message": f"Response from Server {SERVER_ID}",
            "active_requests": active_requests,
            "response_time": round(time.monotonic() - started, 4)
        })
    finally:
        end_request()


@app.route("/status", methods=["GET"])
def status():
    with request_lock:
        current_active = active_requests
    resources = get_resources()
    return jsonify({
        "server_id": SERVER_ID,
        "server_port": PORT,
        "status": "UP",
        "active_requests": current_active,
        "cpu_usage": resources["cpu"],
        "memory_usage": resources["memory"],
        "active_processes": resources["processes"]
    })


@app.route("/process-chunk", methods=["POST"])
def process_chunk():
    """Execute at most one time quantum of a simulated job."""
    payload = request.get_json(silent=True) or {}
    try:
        job_id = int(payload["job_id"])
        quantum = float(payload["quantum"])
        remaining_work = float(payload["remaining_work"])
    except (KeyError, TypeError, ValueError):
        return jsonify({
            "error": "job_id, quantum and remaining_work are required numeric values"
        }), 400

    if quantum <= 0 or remaining_work < 0:
        return jsonify({"error": "quantum must be positive and remaining_work cannot be negative"}), 400

    execution_time = min(quantum, remaining_work)
    begin_request()
    started = time.monotonic()
    try:
        # Cooperative simulation only: this is not OS-level process preemption.
        time.sleep(execution_time)
    finally:
        end_request()

    actual_elapsed = time.monotonic() - started
    new_remaining = max(0.0, remaining_work - execution_time)
    completed = new_remaining <= 1e-9

    return jsonify({
        "job_id": job_id,
        "server_id": SERVER_ID,
        "execution_time": round(actual_elapsed, 4),
        "remaining_work": round(new_remaining, 4),
        "completed": completed
    })


if __name__ == "__main__":
    print(f"Starting backend Server {SERVER_ID} on port {PORT}")
    app.run(host="127.0.0.1", port=PORT, threaded=True)
