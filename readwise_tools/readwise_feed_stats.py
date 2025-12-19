#!/usr/bin/env python3
"""
Readwise Feed Statistics Tool

Analyzes RSS feed subscription data from Readwise Reader.

Setup:
1. Add READWISE_TOKEN to your .env file
2. Run: readwise-feed-stats --days 30

Features:
- Track articles per feed per week
- Monitor "read later" frequency by feed
- Configurable time ranges
- Pretty table output
"""

import os
import argparse
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from urllib.parse import urlparse
from dotenv import load_dotenv
from readwise import ReadwiseReader
from tabulate import tabulate


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze RSS feed statistics from Readwise Reader",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Analyze documents from the last N days"
    )

    parser.add_argument(
        "--weeks",
        type=int,
        help="Analyze documents from the last N weeks (takes precedence over --days)"
    )

    parser.add_argument(
        "--location",
        type=str,
        default="all",
        choices=["all", "later", "archive", "new", "feed", "shortlist"],
        help="Filter by location"
    )

    parser.add_argument(
        "--min-articles",
        type=int,
        default=1,
        help="Only show feeds with at least N articles"
    )

    parser.add_argument(
        "--sort-by",
        type=str,
        default="total",
        choices=["feed", "total", "weekly_avg", "later_count", "later_pct"],
        help="Sort by column"
    )

    parser.add_argument(
        "--category",
        type=str,
        default="rss",
        help="Filter by category (rss, article, email, etc.)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show configuration without making API calls"
    )

    return parser.parse_args()


def calculate_time_range(args):
    """Calculate cutoff date based on --days or --weeks."""
    if args.weeks:
        days = args.weeks * 7
        time_unit = f"{args.weeks} week{'s' if args.weeks != 1 else ''}"
    else:
        days = args.days
        time_unit = f"{args.days} day{'s' if args.days != 1 else ''}"

    # Use timezone-aware datetime to match Readwise API timestamps
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    return cutoff_date, time_unit, days


def extract_domain(url):
    """Extract domain from URL as fallback feed identifier."""
    if not url:
        return "unknown"
    try:
        parsed = urlparse(url)
        return parsed.netloc or "unknown"
    except:
        return "unknown"


def fetch_documents(rw, cutoff_date, args):
    """Fetch documents from Readwise Reader API."""
    # Note: We don't use category in params due to a Readwise API bug
    # that returns malformed JSON when filtering by category.
    # We also can't fetch without any filters due to malformed documents in the full dataset.
    # Instead, we fetch by location separately and combine results.

    all_docs = []

    if args.location != "all":
        # User specified a specific location
        locations_to_fetch = [args.location]
    else:
        # Fetch from all locations separately to avoid the API bug
        locations_to_fetch = ["new", "later", "archive", "feed"]

    if args.verbose:
        print(f"Cutoff date: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"Will filter locally by category: {args.category}")
        print(f"Fetching from locations: {locations_to_fetch}")

    # Fetch from each location separately
    for location in locations_to_fetch:
        if args.verbose:
            print(f"  Fetching from location='{location}'...")

        params = {"location": location}
        location_docs = []

        # Iterate through generator to handle pagination errors gracefully
        try:
            for doc in rw.get_documents(params=params):
                location_docs.append(doc)
        except Exception as e:
            # If we hit an error during pagination (malformed JSON in a document),
            # we keep the documents we successfully retrieved before the error
            if location_docs:
                print(f"  Warning: Error during pagination for '{location}' after {len(location_docs)} docs: {e}")
                if args.verbose:
                    print(f"    Continuing with {len(location_docs)} documents retrieved before error")
            else:
                print(f"  Warning: Error fetching from location '{location}': {e}")
                if args.verbose:
                    import traceback
                    traceback.print_exc()

        all_docs.extend(location_docs)
        if args.verbose and location_docs:
            print(f"    Retrieved {len(location_docs)} documents from '{location}'")

    # Filter by created_at and category
    filtered_docs = []
    for d in all_docs:
        # Check if document has created_at and it's after cutoff
        if hasattr(d, 'created_at') and d.created_at:
            if d.created_at >= cutoff_date:
                # Filter by category locally
                if hasattr(d, 'category') and d.category == args.category:
                    filtered_docs.append(d)
        elif args.verbose:
            print(f"Warning: Document '{getattr(d, 'title', 'Unknown')[:50]}' has no created_at timestamp")

    if args.verbose:
        print(f"Total retrieved: {len(all_docs)} documents across all locations")
        print(f"Filtered to: {len(filtered_docs)} documents (time range + category={args.category})")

    return filtered_docs


def process_documents(documents, args):
    """Process documents and build statistics."""
    feed_stats = defaultdict(lambda: {
        'total': 0,
        'later_count': 0,
        'weeks': defaultdict(int),
        'site_name': '',
        'source': '',
    })

    for doc in documents:
        # Identify feed (priority: site_name > source > domain)
        # Note: For RSS feeds, source is often just "Reader RSS", so site_name is more specific
        feed_id = None

        # Try site_name first (most specific for RSS feeds)
        if hasattr(doc, 'site_name') and doc.site_name:
            feed_id = doc.site_name
        # Fallback to source
        elif hasattr(doc, 'source') and doc.source and doc.source != 'Reader RSS':
            feed_id = doc.source
        # Fallback to domain extraction
        else:
            source_url = getattr(doc, 'source_url', None) or getattr(doc, 'url', None)
            feed_id = extract_domain(source_url)

        if not feed_id or feed_id == 'unknown':
            if args.verbose:
                title = getattr(doc, 'title', 'Unknown')[:50]
                print(f"Warning: Could not identify feed for document '{title}'")
            continue

        stats = feed_stats[feed_id]
        stats['total'] += 1

        # Store metadata (first occurrence only)
        if not stats['site_name'] and hasattr(doc, 'site_name'):
            stats['site_name'] = doc.site_name or ''
        if not stats['source'] and hasattr(doc, 'source'):
            stats['source'] = doc.source or ''

        # Count "read later" items
        if hasattr(doc, 'location') and doc.location == 'later':
            stats['later_count'] += 1

        # Track by week (ISO week)
        if hasattr(doc, 'created_at') and doc.created_at:
            week_key = doc.created_at.strftime('%Y-W%W')
            stats['weeks'][week_key] += 1

    # Calculate aggregates
    for feed_id, stats in list(feed_stats.items()):
        num_weeks = len(stats['weeks'])
        if num_weeks > 0:
            stats['weekly_avg'] = stats['total'] / num_weeks
        else:
            stats['weekly_avg'] = stats['total']

        if stats['total'] > 0:
            stats['later_pct'] = (stats['later_count'] / stats['total']) * 100
        else:
            stats['later_pct'] = 0.0

    # Filter by min_articles
    feed_stats = {
        k: v for k, v in feed_stats.items()
        if v['total'] >= args.min_articles
    }

    return feed_stats


def display_stats(feed_stats, time_unit, days, args):
    """Display statistics as a formatted table."""
    print(f"\nRSS Feed Statistics (Last {time_unit})")
    print("=" * 80)
    print()

    if not feed_stats:
        print("No feeds found matching criteria.")
        return

    # Prepare table data
    table_data = []
    total_articles = 0
    total_later = 0

    for feed_id, stats in feed_stats.items():
        # Use site_name if available, otherwise source, otherwise feed_id
        display_name = stats['site_name'] or stats['source'] or feed_id

        # Truncate long names
        if len(display_name) > 40:
            display_name = display_name[:37] + "..."

        table_data.append([
            display_name,
            stats['total'],
            f"{stats['weekly_avg']:.1f}",
            stats['later_count'],
            f"{stats['later_pct']:.1f}%"
        ])

        total_articles += stats['total']
        total_later += stats['later_count']

    # Sort table based on sort_by argument
    sort_index = {
        'feed': 0,
        'total': 1,
        'weekly_avg': 2,
        'later_count': 3,
        'later_pct': 4
    }.get(args.sort_by, 1)

    # Custom sort to handle numeric vs string values
    def sort_key(row):
        value = row[sort_index]
        if isinstance(value, str):
            if '%' in value:
                return float(value.rstrip('%'))
            try:
                return float(value)
            except ValueError:
                return value
        return value

    table_data.sort(key=sort_key, reverse=True)

    # Display table
    headers = ["Feed Name", "Total", "Weekly Avg", "Read Later", "Later %"]
    print(tabulate(table_data, headers=headers, tablefmt="simple"))

    # Summary
    print(f"\nSummary:")
    print(f"- Total articles: {total_articles}")
    print(f"- Total feeds: {len(feed_stats)}")
    print(f"- Time range: {days} days")
    if total_articles > 0:
        print(f"- Articles with 'Read Later': {total_later} ({total_later/total_articles*100:.1f}%)")

    # Verbose: Per-week breakdown
    if args.verbose:
        print("\n" + "=" * 80)
        print("Per-Week Breakdown:")
        print("=" * 80)

        # Sort feeds by total for verbose output
        sorted_feeds = sorted(feed_stats.items(), key=lambda x: x[1]['total'], reverse=True)

        for feed_id, stats in sorted_feeds[:10]:  # Show top 10 feeds
            display_name = stats['site_name'] or stats['source'] or feed_id
            print(f"\n{display_name}:")
            print(f"  Total: {stats['total']} articles")

            # Sort weeks in reverse chronological order
            weeks_sorted = sorted(stats['weeks'].items(), reverse=True)
            print(f"  Weekly breakdown:")
            for week, count in weeks_sorted[:4]:  # Show last 4 weeks
                print(f"    {week}: {count} articles")

            if len(weeks_sorted) > 4:
                print(f"    ... and {len(weeks_sorted) - 4} more weeks")

            print(f"  Read Later: {stats['later_count']} ({stats['later_pct']:.1f}%)")


def main():
    """Main entry point."""
    load_dotenv()
    READWISE_TOKEN = os.getenv("READWISE_TOKEN")

    if not READWISE_TOKEN:
        print("Error: Missing READWISE_TOKEN in .env file")
        print("Please add your Readwise token to the .env file.")
        return

    # Parse arguments
    args = parse_arguments()

    # Dry run mode
    if args.dry_run:
        print("Dry run mode - showing configuration:")
        if args.weeks:
            print(f"  Time range: {args.weeks} weeks ({args.weeks * 7} days)")
        else:
            print(f"  Time range: {args.days} days")
        print(f"  Location filter: {args.location}")
        print(f"  Category filter: {args.category}")
        print(f"  Minimum articles: {args.min_articles}")
        print(f"  Sort by: {args.sort_by}")
        print(f"  Verbose: {args.verbose}")
        return

    try:
        # Initialize API client
        if args.verbose:
            print("Initializing Readwise Reader client...")
        rw = ReadwiseReader(token=READWISE_TOKEN)

        # Calculate time range
        cutoff_date, time_unit, days = calculate_time_range(args)

        # Fetch documents
        if args.verbose:
            print(f"Fetching documents from the last {time_unit}...")
        documents = fetch_documents(rw, cutoff_date, args)

        if not documents:
            print(f"No documents found in the last {time_unit}.")
            return

        # Process statistics
        if args.verbose:
            print(f"Processing {len(documents)} documents...")
        feed_stats = process_documents(documents, args)

        # Display results
        display_stats(feed_stats, time_unit, days, args)

    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
