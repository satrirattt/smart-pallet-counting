import sqlite3
import unittest
from pathlib import Path


SCHEMA_FILE = Path(__file__).with_name("schema.sql")


class CameraCountSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.connection = sqlite3.connect(":memory:")
        self.schema_sql = SCHEMA_FILE.read_text(encoding="utf-8")
        self.connection.executescript(self.schema_sql)

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
        self.connection.executescript(self.schema_sql)

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

        connection.executescript(self.schema_sql)

        count = connection.execute(
            "SELECT COUNT(*) FROM camera_count_results"
        ).fetchone()[0]
        self.assertEqual(count, 5)
        connection.close()


if __name__ == "__main__":
    unittest.main()
