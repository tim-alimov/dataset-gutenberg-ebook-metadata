# Benchmark

This document records the initial speed check that motivated local metadata
exports.

## Target

Gutendex metadata API:

```text
https://gutendex.com/books/
https://gutendex.com/books/1342/
```

## Date

Tested on 2026-05-03.

## Commands

List endpoint:

```sh
curl -L -s -o /dev/null \
  -w 'http_code=%{http_code}\ntime_total=%{time_total}\ntime_starttransfer=%{time_starttransfer}\nsize_download=%{size_download}\n' \
  https://gutendex.com/books/
```

List endpoint with timeout:

```sh
curl --max-time 15 -L -s -o /dev/null \
  -w 'http_code=%{http_code}\ntime_total=%{time_total}\ntime_starttransfer=%{time_starttransfer}\nsize_download=%{size_download}\nexitcode=%{exitcode}\n' \
  https://gutendex.com/books/
```

Single-book endpoint:

```sh
curl --max-time 30 -L -s -o /dev/null \
  -w 'http_code=%{http_code}\ntime_total=%{time_total}\ntime_starttransfer=%{time_starttransfer}\nsize_download=%{size_download}\nexitcode=%{exitcode}\n' \
  https://gutendex.com/books/1342
```

## Initial Results

| Target | HTTP code | Total time | Time to first byte | Download size | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| `https://gutendex.com/books/` | 200 | 72.324825s | 72.084673s | 58,421 bytes | Slow success |
| `https://gutendex.com/books/` with 15s timeout | 000 | 15.002340s | 0.000000s | 0 bytes | Timeout |
| `https://gutendex.com/books/1342` | 200 | 0.633982s | 0.633701s | 1,660 bytes | Success |

## Interpretation

The result does not prove that Gutendex is always slow. The single-book endpoint
was fast.

The useful claim is narrower:

```text
Bulk/list-style metadata access can be slow from this environment, so local CSV
exports are useful for bulk metadata workflows.
```

Future benchmarks should compare local CSV/Postgres reads against repeated API
requests for common use cases such as filtering by author, category, language,
or format.
