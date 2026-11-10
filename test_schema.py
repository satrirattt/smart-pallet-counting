"""ทดสอบโครงสร้าง SQLite และพฤติกรรมการป้องกันข้อมูลซ้ำ."""

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import init_db
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
            ON CONFLICT DO NOTHING
            """,
            ("2026-11-09T02:00:00.000Z", "CAM-01", 99, "DUPLICATE"),
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
            ("CAM-01", "2026-11-09T02:00:00.000Z"),
        ).fetchone()[0]

        self.assertEqual(new_count, original_count)
        self.assertEqual(stored_count, 3)

    def test_invalid_row_values_are_rejected(self) -> None:
        invalid_timestamps = (
            "not-a-timestamp",
            "2026-11-09T09:00:00+07:00",
            "2026-11-09T02:00:00.0001Z",
            "2026-02-30T00:00:00.000Z",
            "2026-11-31T00:00:00.000Z",
        )
        for timestamp in invalid_timestamps:
            with self.subTest(timestamp=timestamp):
                with self.assertRaisesRegex(
                    sqlite3.IntegrityError, "UTC ISO-8601 with millisecond precision"
                ):
                    self.connection.execute(
                        """
                        INSERT INTO camera_count_results
                            (timestamp, camera_id, object_count, qr_text)
                        VALUES (?, ?, ?, ?)
                        """,
                        (timestamp, "CAM-03", 1, None),
                    )

        invalid_values = (
            ("2026-11-09T03:00:00.000Z", "\t", 1),
            ("2026-11-09T03:00:04.000Z", "\x00", 1),
            ("2026-11-09T03:00:05.000Z", "\u00a0", 1),
            ("2026-11-09T03:00:06.000Z", "\u2003", 1),
            ("2026-11-09T03:00:07.000Z", "\u001c", 1),
            ("2026-11-09T03:00:01.000Z", "CAM-03", "many"),
            ("2026-11-09T03:00:02.000Z", "CAM-03", 1.5),
            ("2026-11-09T03:00:03.000Z", "CAM-03", -1),
        )
        for timestamp, camera_id, object_count in invalid_values:
            with self.subTest(camera_id=camera_id, object_count=object_count):
                with self.assertRaisesRegex(sqlite3.IntegrityError, "must not be blank"):
                    self.connection.execute(
                        """
                        INSERT INTO camera_count_results
                            (timestamp, camera_id, object_count, qr_text)
                        VALUES (?, ?, ?, ?)
                        """,
                        (timestamp, camera_id, object_count, None),
                    )

        with self.assertRaisesRegex(
            sqlite3.IntegrityError, "UTC ISO-8601 with millisecond precision"
        ):
            self.connection.execute(
                "UPDATE camera_count_results SET timestamp = ? WHERE id = 1",
                ("not-a-timestamp",),
            )

        with self.assertRaisesRegex(sqlite3.IntegrityError, "must not be blank"):
            self.connection.execute(
                "UPDATE camera_count_results SET object_count = ? WHERE id = 1",
                ("many",),
            )

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
                timestamp TIMESTAMP,
                camera_id TEXT,
                object_count,
                qr_text TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TRIGGER trg_camera_count_valid_values_insert
            BEFORE INSERT ON camera_count_results
            WHEN 0
            BEGIN
                SELECT RAISE(ABORT, 'outdated trigger');
            END
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

            with self.assertRaisesRegex(sqlite3.IntegrityError, "must not be blank"):
                connection.execute(
                    """
                    INSERT INTO camera_count_results
                        (timestamp, camera_id, object_count)
                    VALUES (?, ?, ?)
                    """,
                    ("2026-11-09T03:00:00.000Z", "\u2003", 1),
                )

            invalid_rows = (
                (None, "CAM-03", 1, None),
                ("2026-11-09T03:00:00.000Z", None, 1, None),
                ("2026-11-09T03:00:01.000Z", "CAM-03", None, None),
            )
            for row in invalid_rows:
                with self.subTest(row=row):
                    with self.assertRaises(sqlite3.IntegrityError):
                        connection.execute(
                            """
                            INSERT INTO camera_count_results
                                (timestamp, camera_id, object_count, qr_text)
                            VALUES (?, ?, ?, ?)
                            """,
                            row,
                        )
        finally:
            connection.close()

        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "legacy.db"
            schema_connection = sqlite3.connect(database_path)
            competing_connection = sqlite3.connect(database_path, timeout=0)
            schema_connection.execute(
                """
                CREATE TABLE camera_count_results (
                    id INTEGER PRIMARY KEY,
                    timestamp TEXT,
                    camera_id TEXT,
                    object_count,
                    qr_text TEXT
                )
                """
            )
            schema_connection.commit()
            inspect_legacy_rows = init_db._inspect_legacy_rows

            def inspect_while_locked(active_connection: sqlite3.Connection):
                with self.assertRaisesRegex(sqlite3.OperationalError, "locked"):
                    competing_connection.execute(
                        """
                        INSERT INTO camera_count_results
                            (timestamp, camera_id, object_count)
                        VALUES (?, ?, ?)
                        """,
                        ("2026-11-09T03:00:00.000Z", "CAM-03", 1),
                    )
                return inspect_legacy_rows(active_connection)

            try:
                with patch(
                    "init_db._inspect_legacy_rows",
                    side_effect=inspect_while_locked,
                ):
                    apply_schema(schema_connection, self.schema_sql)
            finally:
                competing_connection.close()
                schema_connection.close()

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

    def test_existing_invalid_rows_block_schema_upgrade(self) -> None:
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
                (id, timestamp, camera_id, object_count)
            VALUES (?, ?, ?, ?)
            """,
            (42, "not-a-timestamp", "CAM-LEGACY", 1),
        )
        connection.execute(
            """
            INSERT INTO camera_count_results
                (id, timestamp, camera_id, object_count)
            VALUES (?, ?, ?, ?)
            """,
            (43, "2026-11-09T02:01:00Z", "\t", 1),
        )
        connection.execute(
            """
            INSERT INTO camera_count_results
                (id, timestamp, camera_id, object_count)
            VALUES (?, ?, ?, ?)
            """,
            (44, "2026-11-09T02:02:00Z", "CAM-LEGACY", "many"),
        )
        connection.execute(
            """
            INSERT INTO camera_count_results
                (id, timestamp, camera_id, object_count)
            VALUES (?, ?, ?, ?)
            """,
            (45, "2026-11-09T02:03:00Z", "\x00", 1),
        )
        connection.execute(
            """
            INSERT INTO camera_count_results
                (id, timestamp, camera_id, object_count)
            VALUES (?, ?, ?, ?)
            """,
            (46, "2026-11-09T02:04:00Z", "\u2003", 1),
        )
        connection.execute(
            """
            INSERT INTO camera_count_results
                (id, timestamp, camera_id, object_count)
            VALUES (?, ?, ?, ?)
            """,
            (47, "2026-11-09T02:05:00.0001Z", "CAM-LEGACY", 1),
        )

        try:
            with self.assertRaisesRegex(ValueError, "ids: 42, 43, 44, 45, 46, 47"):
                apply_schema(connection, self.schema_sql)

            trigger_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM sqlite_master
                WHERE type = 'trigger' AND tbl_name = 'camera_count_results'
                """
            ).fetchone()[0]
            stored_timestamp = connection.execute(
                "SELECT timestamp FROM camera_count_results WHERE id = 42"
            ).fetchone()[0]
            self.assertEqual(trigger_count, 0)
            self.assertEqual(stored_timestamp, "not-a-timestamp")
            self.assertEqual(
                connection.execute(
                    "SELECT camera_id FROM camera_count_results WHERE id = 43"
                ).fetchone()[0],
                "\t",
            )
            self.assertEqual(
                connection.execute(
                    "SELECT object_count FROM camera_count_results WHERE id = 44"
                ).fetchone()[0],
                "many",
            )
            self.assertEqual(
                connection.execute(
                    "SELECT camera_id FROM camera_count_results WHERE id = 45"
                ).fetchone()[0],
                "\x00",
            )
            self.assertEqual(
                connection.execute(
                    "SELECT camera_id FROM camera_count_results WHERE id = 46"
                ).fetchone()[0],
                "\u2003",
            )
        finally:
            connection.close()

        duplicate_connection = sqlite3.connect(":memory:")
        duplicate_connection.execute(
            """
            CREATE TABLE camera_count_results (
                id INTEGER PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                camera_id TEXT NOT NULL,
                object_count INTEGER NOT NULL,
                qr_text TEXT
            )
            """
        )
        duplicate_connection.executemany(
            """
            INSERT INTO camera_count_results
                (id, timestamp, camera_id, object_count)
            VALUES (?, ?, ?, ?)
            """,
            (
                (1, "2026-11-09T09:00:00+07:00", "CAM-01", 1),
                (2, "2026-11-09T02:00:00Z", "CAM-01", 2),
            ),
        )
        try:
            with self.assertRaisesRegex(ValueError, "ids: 1, 2"):
                apply_schema(duplicate_connection, self.schema_sql)
            trigger_count = duplicate_connection.execute(
                """
                SELECT COUNT(*)
                FROM sqlite_master
                WHERE type = 'trigger' AND tbl_name = 'camera_count_results'
                """
            ).fetchone()[0]
            self.assertEqual(trigger_count, 0)
        finally:
            duplicate_connection.close()


if __name__ == "__main__":
    unittest.main()
