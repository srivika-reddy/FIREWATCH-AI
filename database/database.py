import sqlite3
from datetime import datetime, timezone


def get_connection(database_path):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(database_path):
    with get_connection(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                people_count INTEGER NOT NULL DEFAULT 0,
                animal_count INTEGER NOT NULL DEFAULT 0,
                vehicle_count INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL
            )
            """
        )
        connection.commit()


def add_alert(database_path, alert):
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with get_connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO alerts (timestamp, alert_type, confidence, people_count,
                animal_count, vehicle_count, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (timestamp, alert["alert_type"], alert["confidence"], alert["people_count"],
             alert["animal_count"], alert["vehicle_count"], alert["status"]),
        )
        connection.commit()
        return cursor.lastrowid


def list_alerts(database_path, limit=25):
    with get_connection(database_path) as connection:
        rows = connection.execute(
            "SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]


def clear_alerts(database_path):
    with get_connection(database_path) as connection:
        connection.execute("DELETE FROM alerts")
        connection.commit()
