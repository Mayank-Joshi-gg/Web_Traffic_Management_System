import mysql.connector
from database.db_config import DB_CONFIG


def get_connection():
    """Create and return a MySQL connection."""
    return mysql.connector.connect(**DB_CONFIG)


def _execute_insert(query, values):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(query, values)
        connection.commit()
    except Exception:
        if connection is not None and connection.is_connected():
            connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def log_traffic(server_id, response_time, routing_method):
    query = """
        INSERT INTO traffic_logs (server_id, response_time, routing_method)
        VALUES (%s, %s, %s)
    """
    _execute_insert(query, (server_id, response_time, routing_method))


def log_resources(server_id, cpu, memory, processes, active_requests):
    query = """
        INSERT INTO resource_metrics
        (server_id, cpu_usage, memory_usage, active_processes, active_requests)
        VALUES (%s, %s, %s, %s, %s)
    """
    _execute_insert(query, (server_id, cpu, memory, processes, active_requests))
