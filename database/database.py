import mysql.connector
from database.db_config import DB_CONFIG


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def log_traffic(server_id, response_time, routing_method):
    connection = get_connection()
    cursor = connection.cursor()

    query = '''
        INSERT INTO traffic_logs
        (server_id, response_time, routing_method)
        VALUES (%s, %s, %s)
    '''

    cursor.execute(query, (server_id, response_time, routing_method))
    connection.commit()

    cursor.close()
    connection.close()


def log_resources(server_id, cpu, memory, processes, active_requests):
    connection = get_connection()
    cursor = connection.cursor()

    query = '''
        INSERT INTO resource_metrics
        (server_id, cpu_usage, memory_usage,
         active_processes, active_requests)
        VALUES (%s, %s, %s, %s, %s)
    '''

    cursor.execute(
        query,
        (server_id, cpu, memory, processes, active_requests)
    )

    connection.commit()
    cursor.close()
    connection.close()
