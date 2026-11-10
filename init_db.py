from datetime import datetime
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple


def _inspect_legacy_rows(
    connection: sqlite3.Connection,
) -> Tuple[List[int], List[List[int]]]:
    table_exists = connection.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table' AND name = 'camera_count_results'
        """
    ).fetchone()
    if table_exists is None:
        return [], []

    invalid_ids = []
    timestamp_ids: Dict[Tuple[str, str], List[int]] = {}
    for (
        row_id,
        timestamp,
        sqlite_timestamp,
        camera_id,
        sqlite_camera_id_has_nul,
        sqlite_camera_id_length,
        object_count,
    ) in connection.execute(
        """
        SELECT
            id,
            timestamp,
            strftime('%Y-%m-%dT%H:%M:%fZ', timestamp),
            camera_id,
            instr(camera_id, char(0)),
            length(trim(
                camera_id,
                char(9) || char(10) || char(11) || char(12) || char(13)
                || char(28, 29, 30, 31) || ' '
                || char(133, 160, 5760, 8192, 8193, 8194, 8195, 8196, 8197)
                || char(8198, 8199, 8200, 8201, 8202, 8232, 8233, 8239, 8287, 12288)
            )),
            object_count
        FROM camera_count_results
        """
    ):
        valid_timestamp = False
        try:
            if sqlite_timestamp is None:
                raise ValueError("SQLite cannot parse timestamp")
            parsed_timestamp = datetime.fromisoformat(
                timestamp.replace("Z", "+00:00")
            )
            if parsed_timestamp.utcoffset() is None:
                raise ValueError("timezone is required")
            if parsed_timestamp.microsecond % 1000:
                raise ValueError("sub-millisecond precision is not supported")
            valid_timestamp = True
        except (AttributeError, TypeError, ValueError):
            pass

        valid_camera_id = (
            isinstance(camera_id, str)
            and bool(camera_id.strip(" \t\n\r\v\f"))
            and sqlite_camera_id_has_nul == 0
            and sqlite_camera_id_length is not None
            and sqlite_camera_id_length > 0
        )
        valid_object_count = (
            isinstance(object_count, int) and not isinstance(object_count, bool)
            and object_count >= 0
        )
        if not (valid_timestamp and valid_camera_id and valid_object_count):
            invalid_ids.append(row_id)
            continue

        key = (camera_id, sqlite_timestamp)
        timestamp_ids.setdefault(key, []).append(row_id)

    duplicates = [row_ids for row_ids in timestamp_ids.values() if len(row_ids) > 1]
    return invalid_ids, duplicates


def _execute_schema(connection: sqlite3.Connection, schema_sql: str) -> None:
    statement = ""
    for character in schema_sql:
        statement += character
        if character == ";" and sqlite3.complete_statement(statement):
            connection.execute(statement)
            statement = ""

    if statement.strip():
        raise sqlite3.ProgrammingError("incomplete SQL statement in schema")


def apply_schema(connection: sqlite3.Connection, schema_sql: str) -> None:
    """ติดตั้ง schema ทั้งหมดเป็น transaction เดียว."""
    if connection.in_transaction:
        connection.commit()
    connection.execute("BEGIN IMMEDIATE")
    try:
        invalid_row_ids, duplicate_row_ids = _inspect_legacy_rows(connection)
        if invalid_row_ids:
            ids = ", ".join(str(row_id) for row_id in invalid_row_ids)
            raise ValueError(
                "Existing camera_count_results rows have invalid timestamps, blank "
                "camera_id values, or non-integer/negative object_count values "
                f"(ids: {ids}); correct them before applying the schema"
            )
        if duplicate_row_ids:
            groups = "; ".join(
                ", ".join(str(row_id) for row_id in row_ids)
                for row_ids in duplicate_row_ids
            )
            raise ValueError(
                "Existing camera_count_results rows contain duplicate camera/time "
                f"instants (ids: {groups}); resolve the duplicates before applying the schema"
            )

        _execute_schema(connection, schema_sql)
        connection.commit()
    except BaseException:
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
