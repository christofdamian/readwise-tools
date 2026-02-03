# readwise-tools

A collection of CLI tools for integrating various services with [Readwise Reader](https://readwise.io/read).

## Installation

```bash
pip install -e .
```

Or install dependencies directly:

```bash
pip install requests readwise python-dotenv pycketcasts todoist-api-python tabulate
```

## Configuration

Create a `.env` file in your working directory with the required tokens:

```bash
# Required for all Readwise tools
READWISE_TOKEN=your_readwise_token

# For Mastodon integration
MASTODON_INSTANCE=https://mastodon.social
MASTODON_TOKEN=your_mastodon_token

# For Pocket Casts integration
POCKETCASTS_EMAIL=your_email
POCKETCASTS_PASSWORD=your_password

# For Todoist integration
TODOIST_TOKEN=your_todoist_token

# Browser for opening links (default: firefox)
BROWSER=firefox
```

### Getting Tokens

- **Readwise**: Get your token from https://readwise.io/access_token
- **Mastodon**: Create an application in your Mastodon instance settings under Development
- **Todoist**: Get your token from https://todoist.com/prefs/integrations

## Tools

### mastodon-to-readwise

Sync your Mastodon bookmarks to Readwise Reader.

```bash
mastodon-to-readwise
```

Features:
- Fetches all bookmarks from your Mastodon instance
- Creates documents in Readwise Reader with title, content, and URL
- Tags documents with `mastodon`, `bookmark`, `social`, `mastodon-to-readwise`
- Tracks processed bookmarks in `~/.mastodon_transferred` to avoid duplicates

### pocketcasts-to-readwise

Sync your starred Pocket Casts episodes to Readwise Reader.

```bash
pocketcasts-to-readwise
```

Features:
- Fetches starred episodes from Pocket Casts
- Creates documents with episode title, show notes, and link
- Tags documents with `podcast`, `friday`, `pocketcasts`, `pocketcasts-to-readwise`
- Tracks processed episodes in `~/.pocketcasts_transferred`

### readwise-to-todoist

Export Readwise Reader documents tagged with `todoist` to Todoist tasks.

```bash
readwise-to-todoist
```

Features:
- Fetches documents tagged with `todoist` from Readwise Reader
- Creates Todoist tasks with title, summary, author, and URL
- Labels tasks with `readwise`, `reader`
- Sets due date to today
- Tracks processed documents in `~/.readwise_todoist_transferred`

### readwise-open-links

Open Readwise Reader documents by tag in your browser.

```bash
readwise-open-links --tag friday
readwise-open-links --tag friday --dry-run
readwise-open-links --tag friday --verbose
```

Options:
- `-t, --tag TAG` - Tag to filter by (required)
- `-d, --dry-run` - Show what would be opened without opening tabs
- `-v, --verbose` - Show detailed information

Environment:
- `BROWSER` - Browser to use (default: `firefox`)

### readwise-tag-filter

Tag documents in Readwise Reader matching filter criteria.

```bash
# Tag all articles in 'later' with 'review'
readwise-tag-filter --location later --category article --add-tag review

# Tag videos and podcasts
readwise-tag-filter -c video -c podcast --add-tag watch

# Filter by existing tag
readwise-tag-filter --has-tag important --add-tag priority

# Dry run to preview changes
readwise-tag-filter -c rss --add-tag news --dry-run
```

Options:
- `-l, --location LOCATION` - Filter by location: `new`, `later`, `archive`, `feed`, `shortlist` (default: `later`)
- `-c, --category CATEGORY` - Filter by category (can specify multiple): `article`, `rss`, `video`, `podcast`, `email`
- `--has-tag TAG` - Filter by existing tag
- `-t, --add-tag TAG` - Tag to add to matching documents (required)
- `-d, --dry-run` - Show what would be tagged without making changes
- `-v, --verbose` - Show detailed information

### readwise-feed-stats

Analyze RSS feed statistics from Readwise Reader.

```bash
# Stats for last 30 days (default)
readwise-feed-stats

# Stats for last 2 weeks
readwise-feed-stats --weeks 2

# Stats for last 90 days, sorted by weekly average
readwise-feed-stats --days 90 --sort-by weekly_avg

# Only feeds with 5+ articles
readwise-feed-stats --min-articles 5

# Dry run to show config
readwise-feed-stats --dry-run
```

Options:
- `--days N` - Analyze documents from last N days (default: 30)
- `--weeks N` - Analyze documents from last N weeks (overrides `--days`)
- `--location LOCATION` - Filter by location: `all`, `later`, `archive`, `new`, `feed`, `shortlist` (default: `all`)
- `--category CATEGORY` - Filter by category (default: `rss`)
- `--min-articles N` - Only show feeds with at least N articles (default: 1)
- `--sort-by COLUMN` - Sort by: `feed`, `total`, `weekly_avg`, `later_count`, `later_pct` (default: `total`)
- `-v, --verbose` - Show detailed per-week breakdown
- `--dry-run` - Show configuration without making API calls

Output includes:
- Feed name
- Total articles
- Weekly average
- "Read Later" count and percentage

### readwise-export-links

Export Readwise Reader documents by tag as Markdown or org-mode links.

```bash
# Export as Markdown to stdout
readwise-export-links --tag friday

# Export as org-mode
readwise-export-links --tag friday --org

# Export to file
readwise-export-links --tag reading-list -o links.md

# Dry run
readwise-export-links --tag friday --dry-run
```

Options:
- `-t, --tag TAG` - Tag to filter by (required)
- `--org` - Output in org-mode format instead of Markdown
- `-o, --output FILE` - Output file (default: stdout)
- `-d, --dry-run` - Show config without making API calls
- `-v, --verbose` - Show detailed information

Output format:
- Markdown: `- [Title](URL)` with optional `*[Podcast]*` or `*[YouTube]*` labels
- Org-mode: `- [[URL][Title]]` with optional `/[Podcast]/` or `/[YouTube]/` labels

## State Files

Tools that sync data track processed items to avoid duplicates:

| Tool | State File |
|------|------------|
| mastodon-to-readwise | `~/.mastodon_transferred` |
| pocketcasts-to-readwise | `~/.pocketcasts_transferred` |
| readwise-to-todoist | `~/.readwise_todoist_transferred` |

## License

GPL-3.0 - see [LICENSE](LICENSE) for details.
