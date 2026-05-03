import sqlite3
import os

db_path = "c:\\Users\\rafar\\Downloads\\ContentHive-main\\ContentHive-main\\ContentHub\\ContentInfo.db"
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        print(f"Found {len(rows)} users")
        for row in rows:
            print(dict(row))
    except Exception as e:
        print(f"Error: {e}")
    conn.close()
