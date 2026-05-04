#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import os
import re
import time
from pathlib import Path

try:
    import psycopg
    from psycopg import sql
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: psycopg. Install requirements first: "
        "python3 -m pip install -r requirements.txt"
    ) from exc

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None


LOAD_ORDER = [
    "books",
    "authors",
    "categories",
    "book_authors",
    "book_categories",
    "formats",
]

TABLE_COLUMNS = {
    "books": [
        "id",
        "gutenberg_id",
        "title",
        "issued",
        "rights",
        "media_type",
        "download_count",
        "languages",
        "source_url",
    ],
    "authors": ["id", "source_id", "name", "birth_year", "death_year"],
    "categories": ["id", "name", "type"],
    "book_authors": ["book_id", "author_id", "role"],
    "book_categories": ["book_id", "category_id"],
    "formats": ["id", "book_id", "mime_type", "url", "extent", "modified"],
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--schema", default="public")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--statement-timeout", default="0")
    parser.add_argument("--no-create", action="store_true")
    parser.add_argument("--no-indexes", action="store_true")
    parser.add_argument("--no-truncate", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    started_at = time.perf_counter()
    logging.info("loading environment from %s", args.env_file)
    load_env_file(args.env_file)
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required in the environment or .env file")

    validate_schema_name(args.schema)
    assert_required_files(args.input_dir)

    logging.info("connecting to database")
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            configure_session(cur, args.statement_timeout)
            conn.commit()

            if not args.no_create:
                logging.info("creating schema and tables in schema=%s", args.schema)
                create_schema(cur, args.schema)
                create_tables(cur, args.schema)
                conn.commit()

            if not args.no_truncate:
                logging.info("truncating existing data in schema=%s", args.schema)
                truncate_tables(cur, args.schema)
                conn.commit()

            for table in LOAD_ORDER:
                copy_csv(cur, args.schema, table, args.input_dir / f"{table}.csv")
                conn.commit()

            if not args.no_create and not args.no_indexes:
                logging.info("creating indexes in schema=%s", args.schema)
                create_indexes(cur, args.schema)
                conn.commit()
    logging.info("finished postgres load in %.2fs", time.perf_counter() - started_at)


def validate_schema_name(schema: str) -> None:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", schema):
        raise SystemExit(f"Invalid schema name: {schema!r}")


def load_env_file(path: Path) -> None:
    if not path.exists():
        logging.info("env file not found, using existing environment only")
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        os.environ.setdefault(key, value)


def assert_required_files(input_dir: Path) -> None:
    missing = [f"{table}.csv" for table in LOAD_ORDER if not (input_dir / f"{table}.csv").exists()]
    if missing:
        raise SystemExit(f"Missing CSV files in {input_dir}: {', '.join(missing)}")


def configure_session(cur: psycopg.Cursor, statement_timeout: str) -> None:
    cur.execute(sql.SQL("SET statement_timeout = {}").format(sql.Literal(statement_timeout)))
    logging.info("statement_timeout set to %s", statement_timeout)


def create_schema(cur: psycopg.Cursor, schema: str) -> None:
    cur.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema)))


def create_tables(cur: psycopg.Cursor, schema: str) -> None:
    cur.execute(
        sql.SQL(
            """
            CREATE TABLE IF NOT EXISTS {}.books (
                id integer PRIMARY KEY,
                gutenberg_id integer NOT NULL UNIQUE,
                title text,
                issued date,
                rights text,
                media_type text,
                download_count integer,
                languages text,
                source_url text
            )
            """
        ).format(sql.Identifier(schema))
    )
    cur.execute(
        sql.SQL(
            """
            CREATE TABLE IF NOT EXISTS {}.authors (
                id integer PRIMARY KEY,
                source_id text,
                name text NOT NULL,
                birth_year integer,
                death_year integer
            )
            """
        ).format(sql.Identifier(schema))
    )
    cur.execute(
        sql.SQL(
            """
            CREATE TABLE IF NOT EXISTS {}.categories (
                id integer PRIMARY KEY,
                name text NOT NULL,
                type text NOT NULL,
                UNIQUE (name, type)
            )
            """
        ).format(sql.Identifier(schema))
    )
    cur.execute(
        sql.SQL(
            """
            CREATE TABLE IF NOT EXISTS {}.book_authors (
                book_id integer NOT NULL REFERENCES {}.books(id) ON DELETE CASCADE,
                author_id integer NOT NULL REFERENCES {}.authors(id) ON DELETE CASCADE,
                role text NOT NULL,
                PRIMARY KEY (book_id, author_id, role)
            )
            """
        ).format(sql.Identifier(schema), sql.Identifier(schema), sql.Identifier(schema))
    )
    cur.execute(
        sql.SQL(
            """
            CREATE TABLE IF NOT EXISTS {}.book_categories (
                book_id integer NOT NULL REFERENCES {}.books(id) ON DELETE CASCADE,
                category_id integer NOT NULL REFERENCES {}.categories(id) ON DELETE CASCADE,
                PRIMARY KEY (book_id, category_id)
            )
            """
        ).format(sql.Identifier(schema), sql.Identifier(schema), sql.Identifier(schema))
    )
    cur.execute(
        sql.SQL(
            """
            CREATE TABLE IF NOT EXISTS {}.formats (
                id text PRIMARY KEY,
                book_id integer NOT NULL REFERENCES {}.books(id) ON DELETE CASCADE,
                mime_type text NOT NULL,
                url text NOT NULL,
                extent integer,
                modified timestamp
            )
            """
        ).format(sql.Identifier(schema), sql.Identifier(schema))
    )


def create_indexes(cur: psycopg.Cursor, schema: str) -> None:
    statements = [
        "CREATE INDEX IF NOT EXISTS books_title_idx ON {schema}.books USING btree (title)",
        "CREATE INDEX IF NOT EXISTS authors_name_idx ON {schema}.authors USING btree (name)",
        "CREATE INDEX IF NOT EXISTS categories_name_idx ON {schema}.categories USING btree (name)",
        "CREATE INDEX IF NOT EXISTS categories_type_idx ON {schema}.categories USING btree (type)",
        "CREATE INDEX IF NOT EXISTS book_authors_author_id_idx ON {schema}.book_authors USING btree (author_id)",
        "CREATE INDEX IF NOT EXISTS book_categories_category_id_idx ON {schema}.book_categories USING btree (category_id)",
        "CREATE INDEX IF NOT EXISTS formats_book_id_idx ON {schema}.formats USING btree (book_id)",
        "CREATE INDEX IF NOT EXISTS formats_mime_type_idx ON {schema}.formats USING btree (mime_type)",
    ]
    for statement in statements:
        cur.execute(sql.SQL(statement).format(schema=sql.Identifier(schema)))


def truncate_tables(cur: psycopg.Cursor, schema: str) -> None:
    table_names = [
        sql.SQL("{}.{}").format(sql.Identifier(schema), sql.Identifier(table))
        for table in reversed(LOAD_ORDER)
    ]
    cur.execute(sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE").format(sql.SQL(", ").join(table_names)))


def copy_csv(cur: psycopg.Cursor, schema: str, table: str, path: Path) -> None:
    started_at = time.perf_counter()
    columns = [sql.Identifier(column) for column in TABLE_COLUMNS[table]]
    query = sql.SQL(
        "COPY {}.{} ({}) FROM STDIN WITH (FORMAT csv, HEADER true, NULL '')"
    ).format(
        sql.Identifier(schema),
        sql.Identifier(table),
        sql.SQL(", ").join(columns),
    )
    with path.open("r", encoding="utf-8", newline="") as handle:
        with cur.copy(query) as copy:
            if tqdm is None:
                while chunk := handle.read(1024 * 1024):
                    copy.write(chunk)
            else:
                with tqdm(
                    total=path.stat().st_size,
                    desc=table,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                ) as progress:
                    while chunk := handle.read(1024 * 1024):
                        copy.write(chunk)
                        progress.update(len(chunk.encode("utf-8")))
    logging.debug("loaded %s into %s.%s in %.2fs", path, schema, table, time.perf_counter() - started_at)


if __name__ == "__main__":
    main()
