# Schema

This dataset exports Project Gutenberg ebook metadata into six CSV tables.

The structure is relational because one book can have many authors, categories,
and file formats.

## Relationships

```text
books.id -> book_authors.book_id -> authors.id
books.id -> book_categories.book_id -> categories.id
books.id -> formats.book_id
```

The CSV files can be used without PostgreSQL, but these relationships describe
how the tables fit together.

## books.csv

One row per Project Gutenberg ebook.

| Column | Description |
| --- | --- |
| `id` | Internal book ID. Same value as `gutenberg_id`. |
| `gutenberg_id` | Original Project Gutenberg ebook ID. |
| `title` | Ebook title from the RDF metadata. |
| `issued` | Date the ebook was issued by Project Gutenberg. |
| `rights` | Rights statement from Project Gutenberg. |
| `media_type` | Media type, usually `Text`. |
| `download_count` | Download count from the RDF metadata. |
| `languages` | Language codes joined by `; ` when multiple exist. |
| `source_url` | Project Gutenberg ebook page URL. |

## authors.csv

One row per unique author or contributor.

| Column | Description |
| --- | --- |
| `id` | Internal author ID. |
| `source_id` | Project Gutenberg agent ID when available. |
| `name` | Person name from the RDF metadata. |
| `birth_year` | Birth year when available. |
| `death_year` | Death year when available. |

## categories.csv

One row per unique category value.

| Column | Description |
| --- | --- |
| `id` | Internal category ID. |
| `name` | Category name from the RDF metadata. |
| `type` | Category type: `subject` or `bookshelf`. |

`subject` values come from RDF subjects. `bookshelf` values come from Project
Gutenberg bookshelf metadata.

## book_authors.csv

Join table between books and authors.

| Column | Description |
| --- | --- |
| `book_id` | References `books.id`. |
| `author_id` | References `authors.id`. |
| `role` | Relationship role, currently `author` or `translator`. |

## book_categories.csv

Join table between books and categories.

| Column | Description |
| --- | --- |
| `book_id` | References `books.id`. |
| `category_id` | References `categories.id`. |

## formats.csv

One row per downloadable file format listed in the RDF metadata.

| Column | Description |
| --- | --- |
| `id` | Internal format ID in `{book_id}-{index}` form. |
| `book_id` | References `books.id`. |
| `mime_type` | File MIME type, such as `text/html` or `application/epub+zip`. |
| `url` | Download URL from Project Gutenberg. |
| `extent` | File size in bytes when available. |
| `modified` | Last modified timestamp when available. |

## Notes

- Empty CSV values are treated as `NULL` by the Postgres loader.
- `books.id` and `books.gutenberg_id` currently use the same value.
- The importer skips RDF files inside archive `test/` paths.
- Duplicate Gutenberg IDs are ignored after the first valid book record.

## Current Generated Size

Current local CSV record counts, excluding headers:

```text
89833    books.csv
26823    authors.csv
42697    categories.csv
79073    book_authors.csv
470438   book_categories.csv
2187291  formats.csv
```

`formats.csv` is much larger than the book table because Project Gutenberg lists
many downloadable file variants per ebook.
