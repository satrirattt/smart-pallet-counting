import sqlite3
from pathlib import Path


def apply_schema(connection: sqlite3.Connection, schema_sql: str) -> None:
    """ติดตั้ง schema ทั้งหมดเป็น transaction เดียว."""
    try:
        connection.executescript(f"BEGIN IMMEDIATE;\n{schema_sql}\nCOMMIT;")
    except sqlite3.Error:
        connection.rollback()
        raise


def main() -> None:
    """สร้างฐานข้อมูลในโฟลเดอร์โปรเจกต์และติดตั้ง schema."""
    project_dir = Path(__file__).resolve().parent
    database_path = project_dir / "camera_counts.db"
    schema_path = project_dir / "schema.sql"

    # เปิดฐานข้อมูล แล้วรันสคริปต์ SQL ที่สร้างตารางและข้อมูลตัวอย่าง
    connection = sqlite3.connect(database_path)
    try:
        schema_sql = schema_path.read_text(encoding="utf-8")
        apply_schema(connection, schema_sql)
    finally:
        # ปิด connection เสมอ แม้การอ่าน schema หรือ SQL จะเกิดข้อผิดพลาด
        connection.close()

    print(f"SQLite database ready: {database_path}")


if __name__ == "__main__":
    main()
