# Claude Code Guidelines

## Git Commits

**Do not add Claude Code attribution to commit messages.**

- No "Generated with Claude Code" footer
- No "Co-Authored-By: Claude Sonnet" attribution
- Keep commit messages clean and professional

---

## Project Information: readwise-tools

### Project Structure

This is a Python package (`readwise-tools`) containing CLI tools for integrating various services with Readwise Reader.

**Architecture Pattern**: ETL (Extract-Transform-Load) with state file tracking
- Tools fetch data from external services
- Transform to Readwise format
- Create documents via Readwise API
- Track processed items in state files (`~/.service_transferred`)

**Console Scripts**: Registered in `pyproject.toml` under `[project.scripts]`
- Pattern: `tool-name = "readwise_tools.module_name:main"`

**Existing Tools**:
- `mastodon-to-readwise` - Sync Mastodon bookmarks
- `pocketcasts-to-readwise` - Sync Pocket Casts starred episodes
- `readwise-to-todoist` - Export tagged documents to Todoist
- `readwise-open-links` - Open documents by tag in browser
- `readwise-tag-filter` - Tag documents matching filter criteria
- `readwise-feed-stats` - Analyze RSS feed statistics

### Readwise Reader API - Critical Information

**Python Package**: `readwise` (installed via pip)
- Main class: `ReadwiseReader(token=READWISE_TOKEN)`
- Method: `rw.get_documents(params={...})` - returns Generator

**Known API Bugs** ⚠️:
1. **Category filtering returns malformed JSON**
   - Using `params={"category": "rss"}` causes "Unterminated string" errors
   - **Workaround**: Fetch all, filter by `doc.category` locally

2. **Some locations contain malformed documents**
   - `location="archive"` and `location="feed"` have corrupt documents
   - Error occurs during pagination (after 100-700+ documents)
   - **Workaround**: Iterate with try/catch, keep documents retrieved before error

3. **Fetching without filters hits malformed documents**
   - Calling `get_documents()` with no params will eventually error
   - **Workaround**: Fetch by location separately (`new`, `later`, `archive`, `feed`)

**Document Attributes** (ReadwiseReaderDocument):
- `id` - string, unique identifier
- `title` - string, document title
- `source_url` / `url` - string, original URL
- `created_at` - **datetime (timezone-aware!)**, when added to Reader
- `updated_at` - datetime (timezone-aware)
- `published_date` - string (may be None)
- `category` - string: `"rss"`, `"article"`, `"email"`, `"podcast"`, `"video"`, etc.
- `location` - string: `"new"`, `"later"`, `"archive"`, `"feed"`, `"shortlist"`
- `tags` - dict, tag information
- `source` - string, **for RSS feeds this is often just `"Reader RSS"`** (not unique!)
- `site_name` - string, **use THIS for RSS feed identification** (e.g., "lethain.com", "jwz.org")
- `author` - string
- `summary` - string
- `word_count` - int
- `parent_id` - string or None
- `reading_progress` - float

**RSS Feed Identification**:
- ❌ Don't use `source` - it's generic "Reader RSS" for most RSS feeds
- ✅ Use `site_name` - this contains the actual feed name/domain
- Fallback chain: `site_name` → `source` (if not "Reader RSS") → domain from `source_url`

**Timezone Handling**:
- API returns timezone-aware datetimes
- Use `datetime.now(timezone.utc)` for comparisons
- Don't use naive `datetime.now()` - will cause comparison errors

**API Rate Limiting**:
- 20 requests per minute for `/list/` endpoint
- The `readwise` package handles retries automatically (with warnings)
- Use `get_pagination_limit_20()` internally for compliance

**Query Parameters**:
- `location`: filter by location (works reliably)
- `tag`: filter by tag (may not work reliably, use local filtering)
- `category`: ⚠️ BROKEN - causes malformed JSON (filter locally)
- `updatedAfter`: filters by modification time, not creation time
- `pageCursor`: handled automatically by pagination

### Best Practices for This Project

1. **Error Handling**: Always wrap API calls with try/catch, especially when iterating generators
2. **Pagination Errors**: Iterate through generators manually, keep partial results on error
3. **Local Filtering**: Filter by category, tags, etc. after fetching, not via API params
4. **Timezone Aware**: Always use `timezone.utc` for datetime operations
5. **State Files**: Use `~/.tool_name_state` pattern for tracking processed items
6. **Verbose Mode**: Include `--verbose` flag for debugging, use argparse
7. **Dry Run**: Include `--dry-run` flag to show config without API calls
8. **Tool Pattern**: Follow existing tools (see `readwise_open_links.py` for best example)
