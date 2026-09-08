from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from config import DB_PATH
from database.schema import SCHEMA_SQL


class Database:
    def __init__(self, path: Path | str = DB_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = duckdb.connect(str(self.path))
        self.conn.execute(SCHEMA_SQL)

    def close(self) -> None:
        self.conn.close()

    def replace_frame(self, table: str, frame: pd.DataFrame) -> None:
        self.conn.register("incoming_frame", frame)
        self.conn.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM incoming_frame")
        self.conn.unregister("incoming_frame")

    def append_frame(self, table: str, frame: pd.DataFrame) -> None:
        if frame.empty:
            return
        self.conn.register("incoming_frame", frame)
        self.conn.execute(f"INSERT INTO {table} BY NAME SELECT * FROM incoming_frame")
        self.conn.unregister("incoming_frame")

    def query(self, sql: str, params: list | None = None) -> pd.DataFrame:
        return self.conn.execute(sql, params or []).fetchdf()

    def table_exists(self, table: str) -> bool:
        return bool(self.conn.execute(
            "SELECT count(*) FROM information_schema.tables WHERE table_name=?", [table]
        ).fetchone()[0])
