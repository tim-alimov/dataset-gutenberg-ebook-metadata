# Product Spec

## Purpose

Provide Project Gutenberg ebook metadata as clean, local, relational CSV files.
The project is for users who want bulk metadata without repeatedly calling a
public API or writing their own RDF parser.

## Users

- Developers building ebook catalog, search, or recommendation products.
- Data users who want Gutenberg metadata in CSV form.
- API developers who need relational tables for books, authors, categories, and
  formats.
- PostgreSQL users who want a ready import path for Gutenberg metadata.

## Included

- A downloader for the official Project Gutenberg RDF archive.
- An importer that converts RDF book records into CSV tables.
- A PostgreSQL loader that creates relational tables and indexes.
- Documentation for provenance, schema, import behavior, and benchmark context.

## Not Included

- Full ebook text.
- Cleaned book content.
- Cover image downloads.
- A public API server.
- A web application.

Those can be built as separate projects on top of the generated CSV or
PostgreSQL tables.

## Design Choices

The dataset is normalized because Gutenberg records can have many authors,
subjects, bookshelves, and downloadable file formats. The CSV shape is meant to
work both in simple data tools and in relational databases.

The source of truth is the official Project Gutenberg RDF archive. Gutendex is a
useful JSON API for exploration and comparison, but this project uses RDF because
it is the official bulk metadata source.

## Success Criteria

- A user can regenerate the dataset from the official RDF archive.
- The generated files are understandable without reading importer code.
- PostgreSQL loading works with one command after `DATABASE_URL` is configured.
- Documentation points users to the right detail page instead of repeating the
  same setup and schema material in every file.
