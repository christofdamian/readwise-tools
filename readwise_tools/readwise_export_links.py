#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv
from readwise import ReadwiseReader
import argparse
import logging

load_dotenv()

READWISE_TOKEN = os.getenv("READWISE_TOKEN")


def format_markdown(title, url, label=None):
    """Format a link as Markdown."""
    suffix = f" *[{label}]*" if label else ""
    return f"- [{title}]({url}){suffix}"


def format_org(title, url, label=None):
    """Format a link as org-mode."""
    suffix = f" /[{label}]/" if label else ""
    return f"- [[{url}][{title}]]{suffix}"


def get_document_label(doc):
    """Determine a label for the document based on category or URL."""
    url = doc.source_url
    category = doc.category if hasattr(doc, 'category') else None

    if category == 'podcast' or 'pocketcasts.com' in url or 'pca.st' in url:
        return 'Podcast'
    if category == 'video' or 'youtube.com' in url or 'youtu.be' in url:
        return 'YouTube'
    return None


def main():
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    if not READWISE_TOKEN:
        print("Missing environment variables. Check your .env file.")
        print("Required: READWISE_TOKEN")
        return

    parser = argparse.ArgumentParser(
        description="Export Reader links for a tag as Markdown or org-mode",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("-t", "--tag", help="tag to filter by", required=True)
    parser.add_argument("--org", action="store_true", help="output in org-mode format instead of Markdown")
    parser.add_argument("-o", "--output", help="output file (default: stdout)")
    parser.add_argument("-d", "--dry-run", action="store_true", help="show config without making API calls")
    parser.add_argument("-v", "--verbose", action="store_true", help="output detailed information for debugging")
    args = parser.parse_args()

    tag_to_filter = args.tag
    formatter = format_org if args.org else format_markdown

    if args.dry_run:
        print("Dry run mode - configuration:")
        print(f"  Tag: {tag_to_filter}")
        print(f"  Format: {'org-mode' if args.org else 'Markdown'}")
        print(f"  Output: {args.output if args.output else 'stdout'}")
        return

    try:
        rw = ReadwiseReader(token=READWISE_TOKEN)

        if args.verbose:
            print(f"Querying Readwise Reader API...")
            print(f"Fetching all documents from location='later'...")

        # Fetch all documents from 'later' location
        all_documents = list(rw.get_documents(params={"location": "later"}))

        if args.verbose:
            print(f"Received {len(all_documents)} documents from API")
            print(f"Filtering locally by tag: '{tag_to_filter}'...")

        # Filter documents by tag locally (API tag filtering doesn't seem to work)
        documents = [d for d in all_documents if hasattr(d, 'tags') and d.tags and tag_to_filter in d.tags]

        if args.verbose:
            print(f"Found {len(documents)} documents with tag '{tag_to_filter}'\n")

        lines = []
        for d in documents:
            title = d.title if hasattr(d, 'title') and d.title else d.source_url
            label = get_document_label(d)

            if args.verbose:
                print(f"Document:")
                print(f"  Title: {title}")
                print(f"  URL: {d.source_url}")
                print(f"  Category: {d.category if hasattr(d, 'category') else 'N/A'}")
                print(f"  Tags: {', '.join(d.tags) if hasattr(d, 'tags') and d.tags else 'None'}")
                print()

            lines.append(formatter(title, d.source_url, label))

        output_text = "\n".join(lines)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(output_text + "\n")
            print(f"Exported {len(documents)} links with tag '{tag_to_filter}' to {args.output}")
        else:
            print(output_text)

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
