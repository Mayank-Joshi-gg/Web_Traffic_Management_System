from flask import Flask, jsonify, request
import requests
import time

from monitoring.resource_monitor import get_resources
from database.database import log_traffic, log_resources

app = Flask(__name__)

SERVERS = [
    {"id": 1, "url": "http://127.0.0.1:5001"},
    {"id": 2, "url": "http://127.0.0.1:5002"},
    {"id": 3, "url": "http://127.0.0.1:5003"}
]

round_robin_index = 0


def get_active_requests(server):
    try:
        response = requests.get(server["url"] + "/status", timeout=1)
        return response.json()["active_requests"]
    except:
        return 999


def choose_round_robin():
    global round_robin_index

    server = SERVERS[round_robin_index]
    round_robin_index = (round_robin_index + 1) % len(SERVERS)

    return server


def choose_resource_aware():
    best_server = None
    best_score = float("inf")

    resources = get_resources()

    for server in SERVERS:
        active = get_active_requests(server)

        # Simple score for this academic prototype.
        score = (
            resources["cpu"] * 0.4
            + resources["memory"] * 0.3
            + active * 10 * 0.3
        )

        if score < best_score:
            best_score = score
            best_server = server

        try:
            log_resources(
                server["id"],
                resources["cpu"],
                resources["memory"],
                resources["processes"],
                active
            )
        except Exception as error:
            print("Database resource log skipped:", error)

    return best_server


@app.route("/")
def home():
    return jsonify({
        "project": "Resource-Aware Predictive Web Traffic Management System",
        "message": "Load balancer is running"
    })


@app.route("/request")
def handle_request():
    method = request.args.get("method", "resource")

    if method == "round_robin":
        server = choose_round_robin()
    else:
        server = choose_resource_aware()
        method = "resource_aware"

    start = time.time()

    try:
        response = requests.get(server["url"], timeout=3)
        response_time = time.time() - start

        try:
            log_traffic(
                server["id"],
                response_time,
                method
            )
        except Exception as error:
            print("Database traffic log skipped:", error)

        data = response.json()
        data["routing_method"] = method
        data["load_balancer_response_time"] = round(response_time, 4)

        return jsonify(data)

    except requests.RequestException as error:
        return jsonify({
            "error": "Selected server is unavailable",
            "details": str(error)
        }), 503


@app.route("/test")
def test():
    count = int(request.args.get("count", 10))
    method = request.args.get("method", "resource")

    results = []

    for i in range(count):
        start = time.time()

        if method == "round_robin":
            server = choose_round_robin()
        else:
            server = choose_resource_aware()

        try:
            response = requests.get(server["url"], timeout=3)
            elapsed = time.time() - start

            try:
                log_traffic(server["id"], elapsed, method)
            except Exception as error:
                print("Database traffic log skipped:", error)

            results.append({
                "request": i + 1,
                "server": server["id"],
                "response_time": round(elapsed, 4)
            })

        except requests.RequestException:
            results.append({
                "request": i + 1,
                "server": server["id"],
                "error": "server unavailable"
            })

    return jsonify({
        "routing_method": method,
        "total_requests": count,
        "results": results
    })


if __name__ == "__main__":
    app.run(port=5000, debug=False)
