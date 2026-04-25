import sqlite3
from datetime import datetime, date, timedelta

DB_PATH = "fitmore.db"


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE,
                weight REAL,
                workout TEXT,
                diet TEXT,
                note TEXT,
                calories_burned REAL,
                calories_intake REAL,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        # 兼容旧数据库，已存在的表补充新列
        for col in ("calories_burned REAL", "calories_intake REAL"):
            try:
                conn.execute(f"ALTER TABLE daily_logs ADD COLUMN {col}")
            except Exception:
                pass


def upsert_record(date_str, weight, workout, diet, note, calories_burned, calories_intake):
    now = datetime.now().isoformat()
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM daily_logs WHERE date = ?", (date_str,)
        ).fetchone()
        if existing:
            conn.execute(
                """UPDATE daily_logs
                   SET weight=?, workout=?, diet=?, note=?,
                       calories_burned=?, calories_intake=?, updated_at=?
                   WHERE date=?""",
                (weight, workout, diet, note, calories_burned, calories_intake, now, date_str),
            )
        else:
            conn.execute(
                """INSERT INTO daily_logs
                   (date, weight, workout, diet, note, calories_burned, calories_intake, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (date_str, weight, workout, diet, note, calories_burned, calories_intake, now, now),
            )


def get_all_records():
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT date, weight, workout, diet, note, calories_burned, calories_intake
               FROM daily_logs ORDER BY date DESC"""
        ).fetchall()
    return rows


def delete_record(date_str):
    with get_conn() as conn:
        conn.execute("DELETE FROM daily_logs WHERE date = ?", (date_str,))


def get_last_7_days():
    cutoff = (date.today() - timedelta(days=6)).isoformat()
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT date, weight, workout, diet, note, calories_burned, calories_intake
               FROM daily_logs
               WHERE date >= ?
               ORDER BY date ASC""",
            (cutoff,),
        ).fetchall()
    return rows
