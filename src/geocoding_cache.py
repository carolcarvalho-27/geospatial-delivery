
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class GeocodingCache:
    def __init__(self, database_path="data/geocoding_cache.db"):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS geocoding_cache (
                    address TEXT PRIMARY KEY,
                    latitude REAL,
                    longitude REAL,
                    status TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CHECK (status IN ('found', 'not_found')),
                    CHECK (
                        (status = 'found'
                         AND latitude IS NOT NULL
                         AND longitude IS NOT NULL)
                        OR
                        (status = 'not_found'
                         AND latitude IS NULL
                         AND longitude IS NULL)
                    )
                )
            """)


    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path)

        try:
            with connection:
                yield connection
        finally:
            connection.close()


    def get(self, address):
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT latitude, longitude, status
                FROM geocoding_cache
                WHERE address = ?
                """,
                (address,),
            ).fetchone()

        if row is None:
            return None

        return {
            "latitude": row[0],
            "longitude": row[1],
            "status": row[2],
        }

    def save_found(self, address, latitude, longitude):
        if not -90 <= latitude <= 90:
            raise ValueError("Latitude inválida.")

        if not -180 <= longitude <= 180:
            raise ValueError("Longitude inválida.")

        self._save(address, latitude, longitude, "found")

    def save_not_found(self, address):
        self._save(address, None, None, "not_found")

    def _save(self, address, latitude, longitude, status):
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO geocoding_cache
                    (address, latitude, longitude, status, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(address) DO UPDATE SET
                    latitude = excluded.latitude,
                    longitude = excluded.longitude,
                    status = excluded.status,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (address, latitude, longitude, status),
            )

    def count(self):
        with self._connect() as connection:
            return connection.execute(
                "SELECT COUNT(*) FROM geocoding_cache"
            ).fetchone()[0]
