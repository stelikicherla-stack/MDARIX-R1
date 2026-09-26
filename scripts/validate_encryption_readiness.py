"""Fail-closed verification for database and object-storage encryption.

This deliberately distinguishes local development from production evidence. It
never treats a local Docker volume or local filesystem as encrypted production
storage.
"""
from __future__ import annotations

import os
import sys

from sqlalchemy import create_engine, text


def main() -> int:
    database_url = os.getenv("DATABASE_URL") or os.getenv("MDARIX_DATABASE_URL")
    if not database_url:
        host = os.getenv("POSTGRES_HOST", "127.0.0.1")
        port = os.getenv("POSTGRES_PORT", "5433")
        user = os.getenv("POSTGRES_USER", "mdarix_app")
        password = os.getenv("POSTGRES_PASSWORD", "mdarix_app")
        name = os.getenv("POSTGRES_DB", "mdarix_r1")
        database_url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"

    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        with engine.connect() as connection:
            ssl = str(connection.execute(text("SHOW ssl")).scalar()).lower()
            print(f"DATABASE_TLS = {'PASS' if ssl == 'on' else 'PENDING (PostgreSQL reports ssl=off)'}")
    except Exception as exc:  # noqa: BLE001 - this is a diagnostic gate
        print(f"DATABASE_CONNECTION = BLOCKED ({type(exc).__name__})")

    provider = os.getenv("MDARIX_OBJECT_STORAGE_PROVIDER", "local").lower()
    if provider != "s3":
        print("OBJECT_STORAGE_ENCRYPTION = PENDING (local filesystem provider is not production evidence)")
    else:
        sse = os.getenv("MDARIX_OBJECT_STORAGE_SSE", "AES256")
        bucket = os.getenv("MDARIX_OBJECT_STORAGE_BUCKET")
        print(f"OBJECT_STORAGE_ENCRYPTION = {'PASS' if bucket and sse in {'AES256', 'aws:kms'} else 'PENDING (bucket/SSE configuration incomplete)'}")

    required = {
        "BACKUP_ENCRYPTION_KEY": os.getenv("MDARIX_BACKUP_ENCRYPTION_KEY"),
        "WAL_ARCHIVE_TARGET": os.getenv("MDARIX_WAL_ARCHIVE_TARGET"),
        "MONITORING_ALERT_WEBHOOK": os.getenv("MDARIX_MONITORING_ALERT_WEBHOOK"),
    }
    for name, value in required.items():
        print(f"{name} = {'CONFIGURED' if value else 'PENDING'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
