from flask import Flask, jsonify, request
import requests
import time
import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from prediction.traffic_prediction import predict_traffic
from database.database import log_traffic

app = Flask(__name__)

# Backend server configuration.
SERVERS = [
    {"id": 1, "url": "http://127.0.0.1:5001"},
    {"id": 2, "url": "http://127.0.0.1:5002"},
    {"id": 3, "url": "http://127.0.0.1:5003"}
]

round_robin_index = 0
routing_lock = threading.Lock()


# --------------------------------------------------
# ROUND ROBIN LOAD BALANCING
# --------------------------------------------------

def choose_round_robin():
    """Choose servers in circular order."""
    global round_robin_index

    with routing_lock:
        server = SERVERS[round_robin_index % len(SERVERS)]
        round_robin_index = (
            round_robin_index + 1
        ) % len(SERVERS)

    return server


# --------------------------------------------------
# RESOURCE-AWARE LOAD BALANCING
# --------------------------------------------------

def calculate_load_score(cpu, memory, active_requests):
    """
    Calculate a server load score.

    CPU weight: 50%
    Memory weight: 30%
    Active-request weight: 20%

    Lower score means lower estimated load.
    """

    # Normalize active requests to a scale from 0 to 100.
    active_score = min(
        active_requests / 10.0,
        1.0
    ) * 100

    score = (
        0.5 * cpu
        + 0.3 * memory
        + 0.2 * active_score
    )

    return round(score, 2)


def choose_resource_aware():
    """
    Select the available server with the lowest
    combined CPU, memory, and active-request score.
    """

    server_statuses = []

    # Collect resource information from each server.
    for server in SERVERS:
        try:
            response = requests.get(
                server["url"] + "/status",
                timeout=2
            )

            response.raise_for_status()
            data = response.json()

            if data.get("status") != "UP":
                continue

            cpu = float(data["cpu_usage"])
            memory = float(data["memory_usage"])
            active = int(data["active_requests"])

            # Reject invalid measurements.
            if not (0 <= cpu <= 100):
                continue

            if not (0 <= memory <= 100):
                continue

            if active < 0:
                continue

            score = calculate_load_score(
                cpu,
                memory,
                active
            )

            server_statuses.append({
                "server": server,
                "cpu": cpu,
                "memory": memory,
                "active_requests": active,
                "score": score
            })

        except (
            requests.RequestException,
            ValueError,
            TypeError,
            KeyError
        ):
            # Ignore unavailable servers or invalid responses.
            continue

    if not server_statuses:
        raise RuntimeError(
            "No backend servers are available"
        )

    # Select the server with the lowest score.
    lowest_score = min(
        item["score"] for item in server_statuses
    )

    tied_servers = [
        item for item in server_statuses
        if item["score"] == lowest_score
    ]

    # Rotate among servers with equal scores.
    global round_robin_index

    with routing_lock:
        selected = tied_servers[
            round_robin_index % len(tied_servers)
        ]

        round_robin_index += 1

    # Print metrics for evaluation and debugging.
    print(
        f"Selected Server {selected['server']['id']} | "
        f"CPU: {selected['cpu']}% | "
        f"Memory: {selected['memory']}% | "
        f"Active Requests: {selected['active_requests']} | "
        f"Score: {selected['score']}"
    )

    return selected["server"]


# --------------------------------------------------
# ROUTING METHOD SELECTOR
# --------------------------------------------------

def choose_server(method):
    """Select a server using the requested method."""

    method = method.lower().strip()

    if method == "round_robin":
        return choose_round_robin()

    if method == "resource_aware":
        return choose_resource_aware()

    raise ValueError(
        "Invalid method. Use 'round_robin' or 'resource_aware'."
    )


# --------------------------------------------------
# FORWARD REQUEST TO BACKEND
# --------------------------------------------------

def forward_request(server, routing_method="unknown"):
    """Forward a normal request and save its traffic record."""

    start_time = time.monotonic()

    response = requests.get(
        server["url"] + "/",
        timeout=10
    )

    response.raise_for_status()

    elapsed = time.monotonic() - start_time
    data = response.json()

    # Save every successfully completed normal request for prediction.
    try:
        log_traffic(
            server["id"],
            round(elapsed, 4),
            routing_method
        )
    except Exception as error:
        # A database logging failure should not make a healthy
        # backend request fail. The error remains visible in terminal.
        app.logger.exception("Traffic logging failed: %s", error)

    return {
        "server": server["id"],
        "response_time": round(elapsed, 4),
        "backend_response": data
    }


# --------------------------------------------------
# LOAD BALANCER HOME
# --------------------------------------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Load balancer is running",
        "project": (
            "Resource-Aware Predictive Web Traffic "
            "Management System"
        ),
        "available_methods": [
            "round_robin",
            "resource_aware"
        ]
    })


# --------------------------------------------------
# SINGLE REQUEST
# --------------------------------------------------

@app.route("/request", methods=["GET"])
def single_request():
    method = request.args.get(
        "method",
        "resource_aware"
    ).lower().strip()

    try:
        server = choose_server(method)
        result = forward_request(server, method)

        result["routing_method"] = method

        return jsonify(result)

    except ValueError as error:
        return jsonify({
            "error": str(error)
        }), 400

    except (
        requests.RequestException,
        RuntimeError
    ) as error:
        return jsonify({
            "error": "Could not process the request",
            "details": str(error)
        }), 503


# --------------------------------------------------
# SEQUENTIAL TEST
# --------------------------------------------------

@app.route("/test", methods=["GET"])
def test_requests():
    try:
        count = int(request.args.get("count", 5))

    except (ValueError, TypeError):
        return jsonify({
            "error": "count must be an integer"
        }), 400

    method = request.args.get(
        "method",
        "resource_aware"
    ).lower().strip()

    if not 1 <= count <= 100:
        return jsonify({
            "error": "count must be between 1 and 100"
        }), 400

    if method not in (
        "round_robin",
        "resource_aware"
    ):
        return jsonify({
            "error": (
                "method must be round_robin "
                "or resource_aware"
            )
        }), 400

    results = []

    for request_number in range(1, count + 1):
        try:
            server = choose_server(method)
            result = forward_request(server, method)

            result["request"] = request_number
            result["routing_method"] = method

            results.append(result)

        except (
            requests.RequestException,
            RuntimeError
        ) as error:
            return jsonify({
                "error": "A backend request failed",
                "failed_request": request_number,
                "details": str(error),
                "results": results
            }), 503

    return jsonify({
        "routing_method": method,
        "total_requests": count,
        "results": results
    })


# --------------------------------------------------
# CONCURRENT TEST
# --------------------------------------------------

@app.route("/concurrent-test", methods=["GET"])
def concurrent_test():
    try:
        count = int(request.args.get("count", 10))

        method = request.args.get(
            "method",
            "resource_aware"
        ).lower().strip()

        if not 1 <= count <= 100:
            return jsonify({
                "error": "count must be between 1 and 100"
            }), 400

        if method not in (
            "round_robin",
            "resource_aware"
        ):
            return jsonify({
                "error": "Invalid routing method"
            }), 400

        def run_one_request(number):
            server = choose_server(method)
            result = forward_request(server, method)

            result["request"] = number
            result["routing_method"] = method

            return result

        results = []

        with ThreadPoolExecutor(
            max_workers=min(count, 10)
        ) as executor:

            futures = {
                executor.submit(
                    run_one_request,
                    number
                ): number
                for number in range(1, count + 1)
            }

            for future in as_completed(futures):
                try:
                    results.append(future.result())

                except Exception as error:
                    results.append({
                        "request": futures[future],
                        "error": str(error)
                    })

        results.sort(
            key=lambda item: item["request"]
        )

        return jsonify({
            "routing_method": method,
            "total_requests": count,
            "successful_requests": sum(
                1 for item in results
                if "error" not in item
            ),
            "results": results
        })

    except Exception as error:
        app.logger.exception(
            "Concurrent test failed"
        )

        return jsonify({
            "error": "Concurrent test failed",
            "details": str(error)
        }), 500


# --------------------------------------------------
# TIME-QUANTUM DEMONSTRATION
# --------------------------------------------------

@app.route("/quantum-test", methods=["GET"])
def quantum_test():
    """Run a cooperative, application-level Round Robin simulation."""
    try:
        count = int(request.args.get("count", 3))
        quantum = float(request.args.get("quantum", 2))

        if not 1 <= count <= 20:
            return jsonify({"error": "count must be between 1 and 20"}), 400
        if not 0 < quantum <= 10:
            return jsonify({
                "error": "quantum must be greater than 0 and at most 10"
            }), 400

        # Each job represents a fixed amount of simulated work (seconds).
        work_times = [5.0, 3.0, 7.0]
        jobs = deque([
            {
                "job_id": job_number,
                "remaining_work": work_times[(job_number - 1) % len(work_times)]
            }
            for job_number in range(1, count + 1)
        ])

        results = []
        turn = 0
        # Defensive limit: every turn must reduce remaining work.
        max_turns = sum(
            int((job["remaining_work"] + quantum - 1e-9) // quantum) + 1
            for job in jobs
        ) + count + 5

        while jobs and turn < max_turns:
            job = jobs.popleft()
            turn += 1
            server = choose_round_robin()

            response = requests.post(
                server["url"] + "/process-chunk",
                json={
                    "job_id": job["job_id"],
                    "quantum": quantum,
                    "remaining_work": job["remaining_work"]
                },
                timeout=quantum + 10
            )
            response.raise_for_status()
            data = response.json()

            # Validate backend response before updating the ready queue.
            required = {
                "server_id", "execution_time", "remaining_work", "completed"
            }
            missing = required.difference(data)
            if missing:
                raise ValueError(
                    "Backend /process-chunk response is missing: "
                    + ", ".join(sorted(missing))
                )

            remaining = float(data["remaining_work"])
            if remaining < 0:
                raise ValueError("Backend returned negative remaining_work")

            job["remaining_work"] = remaining
            results.append({
                "turn": turn,
                "job_id": job["job_id"],
                "server": data["server_id"],
                "execution_time": round(float(data["execution_time"]), 4),
                "remaining_work": round(remaining, 4),
                "completed": bool(data["completed"])
            })

            if not bool(data["completed"]):
                # The unfinished job goes to the end of the ready queue.
                jobs.append(job)

        if jobs:
            return jsonify({
                "error": "Maximum scheduling turns exceeded",
                "details": "A job did not finish; check /process-chunk implementation.",
                "results": results
            }), 500

        return jsonify({
            "algorithm": "Time-Quantum Round Robin Demonstration",
            "time_quantum": quantum,
            "total_jobs": count,
            "total_turns": turn,
            "results": results
        })

    except (ValueError, TypeError) as error:
        return jsonify({"error": "Invalid quantum test input", "details": str(error)}), 400
    except Exception as error:
        app.logger.exception("Quantum test failed")
        return jsonify({
            "error": "Quantum test failed",
            "details": str(error)
        }), 500


@app.route("/prediction", methods=["GET"])
def traffic_prediction_api():
    try:
        result = predict_traffic()
        return result, 200

    except Exception as error:
        return {
            "status": "error",
            "message": "Unable to generate traffic prediction.",
            "details": str(error)
        }, 500
# --------------------------------------------------
# START LOAD BALANCER
# --------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        threaded=True
    )
