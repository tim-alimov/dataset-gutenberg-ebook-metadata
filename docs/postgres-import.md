# PostgreSQL Import

The Postgres loader imports generated CSV files into relational tables.

## Requirements

Install dependencies:

```sh
python3 -m pip install -r requirements.txt
```

Create a `.env` file:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/database_name
```

If `DATABASE_URL` is already set in the terminal, that value is used instead of
the `.env` value.

## Run

```sh
python3 scripts/load_postgres.py
```

By default, the loader:

- reads CSV files from `data/processed`
- creates the schema and tables if needed
- creates indexes
- truncates existing data
- disables PostgreSQL `statement_timeout` for the session
- loads CSV data with PostgreSQL `COPY`
- commits after each table is loaded

Indexes are created after data loading. This is faster and helps hosted Postgres
providers avoid timing out during large imports.

## Options

Use another input directory:

```sh
python3 scripts/load_postgres.py --input-dir /path/to/csv-files
```

Use another schema:

```sh
python3 scripts/load_postgres.py --schema gutenberg
```

Use another env file:

```sh
python3 scripts/load_postgres.py --env-file .env.local
```

Skip table creation:

```sh
python3 scripts/load_postgres.py --no-create
```

`--no-create` also skips index creation. Use it only when the target schema,
tables, constraints, and indexes are already managed elsewhere.

Append without truncating:

```sh
python3 scripts/load_postgres.py --no-truncate
```

Show more detailed logs:

```sh
python3 scripts/load_postgres.py --log-level DEBUG
```

Use a custom statement timeout:

```sh
python3 scripts/load_postgres.py --statement-timeout 30min
```

Skip index creation:

```sh
python3 scripts/load_postgres.py --no-indexes
```

## Tables Created

The loader creates:

```text
books
authors
categories
book_authors
book_categories
formats
```

Foreign keys are created for join tables and format rows. The loader creates
indexes after loading data so large imports avoid per-row index maintenance.

The index set is intended for online library API patterns:

- direct book lookups by primary key or `gutenberg_id`
- title, author, and category browsing
- title, author, and category text search with PostgreSQL `pg_trgm` when the
  extension is available
- author/category joins from list endpoints
- filters by category type, author role, language, media type, rights, and MIME
  type
- sorting by newest issue date or highest download count

Language filtering uses a GIN expression index over the CSV-style language list.
For example, an API query can use:

```sql
WHERE string_to_array(languages, '; ') @> ARRAY['en']
```

The loader attempts to enable `pg_trgm` for fast `ILIKE`/similarity search. If a
hosted Postgres provider does not allow that extension, the loader logs a warning
and still creates the core relational indexes.

## Important Behavior

The default import is destructive for existing rows in these tables because it
truncates before loading. Use `--no-truncate` only when you intentionally want to
append data.

For normal full refreshes, keep the default truncation behavior.

The loader commits after each table. If a large table such as `formats` fails on
a hosted provider, already loaded tables remain committed instead of the whole
import rolling back.
