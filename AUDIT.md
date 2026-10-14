# Project Audit

Audit of the initial implementation: bugs found, what was fixed, and the
remaining gaps planned as follow-up work.

## Fixed

### Correctness

| Area | Problem | Fix |
|------|---------|-----|
| Extractor | `extract_from_html` stripped every `<script>` tag *before* reading JSON-LD, so `structured_data` was always empty | Parse JSON-LD first |
| Extractor | Product/article JSON-LD parsing crashed or returned nothing for common valid shapes: string `brand`, string `author`, `offers` as a list, `AggregateOffer`, `image` as a list/ImageObject, `@type` as a list, nodes inside `@graph` | Shared helpers that flatten `@graph`/lists and accept string/object/list values |
| Extractor | Price regex `[\d,]+\.?\d*` matched a bare comma, so the price came out as `""` | `\d[\d,]*(?:\.\d+)?`, and try the next selector when no number is found |
| Extractor | Long pages exceeded spaCy's `max_length` (1M chars) and raised | Cap NER input at 100k chars |
| Storage | SQLAlchemy model declared a column attribute named `metadata`, which is reserved by the declarative API (error on the pinned SQLAlchemy 2.0.23, warning on newer releases) | Map attribute `meta` to column `"metadata"` |
| Storage | Postgres URL was built with an f-string, so passwords containing `@ : / #` broke the connection | `sqlalchemy.engine.URL.create` (and `quote_plus` in `get_postgres_url`) |
| Storage | Postgres `update()` set every unspecified column to `NULL` | Only update fields that were passed |
| Storage | Postgres `find()` didn't return extracted fields such as `price` (they only live in `raw_data`), so price monitoring never worked on Postgres | Merge `raw_data` into returned rows |
| Storage | Mongo `save()` mutated the caller's dict, adding an `ObjectId` that made crawl and Celery results non-JSON-serializable | Save a copy |
| Celery | `monitor_price` saved the new price *before* reading the "previous" one, then read the **oldest** record, so it compared against the first price ever seen (or itself) | Read the newest record before scraping; handle non-numeric prices and a zero previous price |
| Celery | Tasks are routed to the `scraping` queue, but `smart-scraper worker` and the documented `celery` command only consumed the default queue, so tasks were never processed | Worker consumes `scraping,celery` (`-Q` option); docs updated |
| Celery | `scrape_urls_batch` created a new scraper per URL, resetting rate limits and crawl delays for every URL | One scraper per batch |
| Scraper | HTTP 4xx/5xx pages were reported as `success: True` | Record `status_code`; treat >= 400 as failure; crawler skips them |
| Crawler | Followed `mailto:`, `javascript:`, `tel:` links; treated `#fragment` variants as new pages; O(n²) queue membership checks; one DB connection per page | Normalize links, `deque` + `seen` set, one DB connection per crawl |
| Ethics | robots.txt was fetched with `urllib` defaults: no timeout and a `Python-urllib` User-Agent. Many sites answer that with 403, which the stdlib treats as "disallow everything" | Fetch with `requests`, a 10s timeout and a descriptive UA, keeping the stdlib's 401/403/4xx semantics |
| Ethics | robots.txt fetch was blocking inside the event loop | Run in an executor |
| Ethics | robots.txt `Crawl-delay` was parsed but never applied; the cache TTL was never applied | Apply max(robots delay, configured delay); expire the cache entries |
| Ethics | Concurrent requests to the same domain could all pass the rate-limit check and crawl delay at once | Per-domain `asyncio.Lock` |
| Browser | Link selector was formatted into a JS string (a quote in the selector broke the script) | `eval_on_selector_all` |
| Browser | Chromium-only flags were passed to Firefox/WebKit | Only pass them for Chromium |
| Browser | `PROXY_ENABLED` / `PROXY_LIST` were never read | Pick a random proxy from the list |
| CLI | `title[:50]` crashed when a result's title was `None`; `query` loaded the whole collection and leaked the connection on error | Safe formatting; `limit` passed to the DB, newest first, context manager |
| CLI | `setup` called a bare `python` / `playwright` (wrong interpreter in venvs) and ignored failures | `sys.executable -m ...`, `check=True` |

### Packaging and project hygiene

- Importing the package created `data/`, `logs/` and `screenshots/` in the current directory. Directories are now created only when needed.
- `find_packages()` shipped `tests` as a top-level package. It is now excluded.
- `torch` and `transformers` (multiple GB) were hard requirements even though the code treats them as optional. They moved to the `transformers` extra.
- The exact pins (`lxml==4.9.3`, `torch==2.1.1`, …) don't install on current Python versions. They are now lower bounds. `requests>=2.32` (CVE-2024-35195), `transformers>=4.38` (CVE-2024-3568).
- Python 3.8 (EOL) dropped; 3.9–3.12 supported.
- The dev tools moved to `requirements-dev.txt` and the `dev` extra. Unused `scikit-learn`, `python-slugify` and `cachetools` were removed from requirements.
- `browser_type` and `database_type` are validated with `Literal`.
- The docs' `yourusername` URL placeholders now point to the real repository.
- Added GitHub Actions CI (flake8 + pytest on Python 3.9–3.12) and a `setup.cfg` with flake8/pytest config.
- Tests went from 7 to 37. They cover each fix above and need no network, browser, database or broker.

## Remaining gaps (planned)

Priority order. These are larger changes, deliberately left out of this pass.

1. **Browser reuse.** `scrape()` launches a whole browser per URL, so `scrape_multiple` with 5 URLs starts 5 browsers. Plan: share one browser and give each task its own context.
2. **`networkidle` default.** Sites with long-polling or analytics beacons often never reach network idle, so the page times out. Plan: make `wait_until` configurable and default to `load`.
3. **Retries.** `tenacity` is a dependency but unused. Plan: retry transient navigation errors and 5xx/429 with backoff, honoring `Retry-After`.
4. **User-Agent vs robots.txt consistency.** robots.txt is checked for `*` while pages are fetched with random browser User-Agents, which is at odds with the README's "legitimate user agents" claim. Plan: a configurable bot identity used for both, with UA rotation opt-in.
5. **Untrusted input in Celery tasks.** If tasks are exposed to untrusted callers, `url` (SSRF to internal hosts) and `execute_script` need guarding. Plan: a scheme/host allowlist option, and disable `execute_script` in workers by default.
6. **Docker.** INSTALL.md advertises `docker-compose up` as "coming soon". Plan: a Dockerfile and a compose file with Redis and MongoDB.
7. **Postgres querying.** Only `url`/`title` filters are supported. Plan: JSONB queries on `raw_data`.
8. **Coverage.** No browser-level integration tests in CI; mypy isn't run. Plan: Playwright tests against a local fixture server, and mypy in CI.
