import sqlite3
from pathlib import Path

from app.core.config import get_settings

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def run_migrations() -> None:
    settings = get_settings()
    db_path = Path(settings.sqlite_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(SCHEMA_PATH.read_text())
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    run_migrations()
    print("Schema applied.")
