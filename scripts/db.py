"""Shared database helpers for Contract-to-Cash scripts."""

from __future__ import annotations

import os
import sys

import psycopg2
import psycopg2.extensions
import psycopg2.extras

DEC2FLOAT = psycopg2.extensions.new_type(
    psycopg2.extensions.DECIMAL.values,
    "DEC2FLOAT",
    lambda value, curs: float(value) if value is not None else None,
)
psycopg2.extensions.register_type(DEC2FLOAT)


def connect(search_path: str = "public_marts, public_staging, raw, public"):
    """Return a psycopg2 connection with RealDictCursor and search_path set."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        pw = os.environ.get("POSTGRES_PASSWORD", "")
        url = f"postgresql://postgres:REDACTED@localhost:5432/cinderhaven"
    conn = psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)
    with conn.cursor() as cur:
        cur.execute(f"SET search_path TO {search_path}")
    conn.commit()
    return conn
