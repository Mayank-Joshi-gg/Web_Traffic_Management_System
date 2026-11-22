from datetime import datetime, timedelta
from database.database import get_connection

WINDOW_SIZE = 5
HISTORY_MINUTES = 10


def get_historical_traffic(minutes=HISTORY_MINUTES):
    """Return one request count for every minute, including zero-count minutes."""
    if not isinstance(minutes, int) or minutes < 1:
        raise ValueError("minutes must be a positive integer")

    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT
                DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:00') AS minute_bucket,
                COUNT(*) AS request_count
            FROM traffic_logs
            WHERE created_at >= NOW() - INTERVAL %s MINUTE
            GROUP BY minute_bucket
            ORDER BY minute_bucket ASC
        """
        cursor.execute(query, (minutes,))
        rows = cursor.fetchall()

        traffic = {}
        for row in rows:
            minute_value = row["minute_bucket"]
            if isinstance(minute_value, datetime):
                minute = minute_value.replace(second=0, microsecond=0)
            else:
                minute = datetime.strptime(str(minute_value), "%Y-%m-%d %H:%M:%S")
            traffic[minute] = int(row["request_count"])

        now = datetime.now()
        current_minute = now.replace(second=0, microsecond=0)
        # Return the latest `minutes` minute buckets, including this minute.
        first_minute = current_minute - timedelta(minutes=minutes - 1)
        return [
            {
                "minute": (first_minute + timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M"),
                "requests": traffic.get(first_minute + timedelta(minutes=i), 0)
            }
            for i in range(minutes)
        ]
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def calculate_mae(values, window=WINDOW_SIZE):
    """Calculate historical mean absolute error for a moving-average model."""
    if len(values) <= window:
        return None

    errors = []
    for index in range(window, len(values)):
        predicted = sum(values[index - window:index]) / window
        errors.append(abs(values[index] - predicted))

    return round(sum(errors) / len(errors), 2) if errors else None


def predict_traffic():
    """Forecast next-minute request volume using the latest five minute buckets."""
    history = get_historical_traffic(minutes=HISTORY_MINUTES)
    values = [int(item["requests"]) for item in history]

    if not any(values):
        return {
            "status": "no_data",
            "message": "No traffic history found. Send requests through the load balancer first.",
            "actual_traffic": history,
            "predicted_requests": None,
            "window_size": WINDOW_SIZE,
            "mae": None
        }

    recent_values = values[-WINDOW_SIZE:]
    prediction = round(sum(recent_values) / len(recent_values), 2)
    next_minute = datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=1)

    return {
        "status": "success",
        "message": "Traffic prediction generated successfully.",
        "actual_traffic": history,
        "predicted_requests": prediction,
        "prediction_for": next_minute.strftime("%Y-%m-%d %H:%M"),
        "window_size": len(recent_values),
        "mae": calculate_mae(values)
    }
