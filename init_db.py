import sqlite3
from pathlib import Path


def main() -> None:
    project_dir = Path(__file__).resolve().parent
    database_path = project_dir / "camera_counts.db"
    schema_path = project_dir / "schema.sql"

    connection = sqlite3.connect(database_path)
    try:
        with connection:
            connection.executescript(schema_path.read_text(encoding="utf-8"))
    finally:
        connection.close()

    print(f"SQLite database ready: {database_path}")


if __name__ == "__main__":
    main()
