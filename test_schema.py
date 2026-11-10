"""ทดสอบโครงสร้าง SQLite และพฤติกรรมการป้องกันข้อมูลซ้ำ."""

import sqlite3
import unittest
from pathlib import Path

from init_db import apply_schema


SCHEMA_FILE = Path(__file__).with_name("schema.sql")


class CameraCountSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        # ใช้ฐานข้อมูลชั่วคราวเพื่อไม่แก้ไข camera_counts.db ของผู้ใช้
        self.connection = sqlite3.connect(":memory:")
        self.schema_sql = SCHEMA_FILE.read_text(encoding="utf-8")
        apply_schema(self.connection, self.schema_sql)

    def tearDown(self) -> None:
        self.connection.close()

    def test_duplicate_camera_timestamp_is_ignored(self) -> None:
        original_count = self.connection.execute(
            "SELECT COUNT(*) FROM camera_count_results"
        ).fetchone()[0]

        self.connection.execute(
            """
            INSERT INTO camera_count_results
                (timestamp, camera_id, object_count, qr_text)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (camera_id, timestamp) DO NOTHING
            """,
            ("2026-11-09T09:00:00+07:00", "CAM-01", 99, "DUPLICATE"),
        )

        new_count = self.connection.execute(
            "SELECT COUNT(*) FROM camera_count_results"
        ).fetchone()[0]
        stored_count = self.connection.execute(
            """
            SELECT object_count
            FROM camera_count_results
            WHERE camera_id = ? AND timestamp = ?
            """,
            ("CAM-01", "2026-11-09T09:00:00+07:00"),
        ).fetchone()[0]

        self.assertEqual(new_count, original_count)
        self.assertEqual(stored_count, 3)

    def test_running_schema_again_does_not_duplicate_sample_rows(self) -> None:
        apply_schema(self.connection, self.schema_sql)

        count = self.connection.execute(
            "SELECT COUNT(*) FROM camera_count_results"
        ).fetchone()[0]
        self.assertEqual(count, 5)

    def test_schema_adds_duplicate_protection_to_existing_table(self) -> None:
        connection = sqlite3.connect(":memory:")
        connection.execute(
            """
            CREATE TABLE camera_count_results (
                id INTEGER PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                camera_id TEXT NOT NULL,
                object_count INTEGER NOT NULL CHECK (object_count >= 0),
                qr_text TEXT
            )
            """
        )
        connection.execute(
            """
            INSERT INTO camera_count_results
                (timestamp, camera_id, object_count, qr_text)
            VALUES (?, ?, ?, ?)
            """,
            ("2026-11-09T09:00:00+07:00", "CAM-01", 3, "PALLET-A"),
        )

        try:
            apply_schema(connection, self.schema_sql)

            count = connection.execute(
                "SELECT COUNT(*) FROM camera_count_results"
            ).fetchone()[0]
            self.assertEqual(count, 5)
        finally:
            connection.close()

    def test_failed_schema_rolls_back_partial_changes(self) -> None:
        with self.assertRaises(sqlite3.OperationalError):
            apply_schema(
                self.connection,
                "CREATE TABLE partial_table (id INTEGER); INVALID SQL;",
            )

        table_exists = self.connection.execute(
            """
            SELECT COUNT(*)
            FROM sqlite_master
            WHERE type = 'table' AND name = 'partial_table'
            """
        ).fetchone()[0]
        self.assertEqual(table_exists, 0)


if __name__ == "__main__":
    unittest.main()
