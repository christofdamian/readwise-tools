#!/usr/bin/env python3
"""
Archives all Readwise Reader documents matching a given tag.

Example usage:
    # Dry run to see what would be archived
    readwise-archive-tag -t review --dry-run --verbose

    # Archive all documents tagged 'review' from 'later'
    readwise-archive-tag -t review --verbose

    # Archive tagged documents from 'new' location
    readwise-archive-tag -t cleanup -l new
"""

import os
import requests
from dotenv import load_dotenv
from readwise import ReadwiseReader
import argparse
import logging

load_dotenv()

READWISE_TOKEN = os.getenv("READWISE_TOKEN")
READWISE_API_BASE = "https://readwise.io/api/v3"


def archive_document(document_id: str, token: str) -> bool:
    """Archive a document via the Readwise API."""
    url = f"{READWISE_API_BASE}/update/{document_id}/"
    headers = {"Authorization": f"Token {token}"}
    payload = {"location": "archive"}

    response = requests.patch(url, headers=headers, json=payload)
    return response.status_code == 200


def main():
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    if not READWISE_TOKEN:
        print("Missing environment variables. Check your .env file.")
        print("Required: READWISE_TOKEN")
        return

    parser = argparse.ArgumentParser(
        description="Archive documents matching a given tag",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-t", "--tag",
        help="tag to filter by",
        required=True
    )
    parser.add_argument(
        "-l", "--location",
        help="source location to fetch from (new, later, feed, shortlist)",
        default="later"
    )
    parser.add_argument(
        "-d", "--dry-run",
        action="store_true",
        help="show what would be archived without making changes"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="output detailed information for debugging"
    )
    args = parser.parse_args()

    if args.dry_run:
        print("DRY RUN MODE - No changes will be made\n")

    if args.verbose:
        print("Configuration:")
        print(f"  Tag: {args.tag}")
        print(f"  Location: {args.location}")
        print()

    try:
        rw = ReadwiseReader(token=READWISE_TOKEN)

        if args.verbose:
            print(f"Fetching documents from location='{args.location}'...")

        # Fetch documents - use error handling for pagination issues
        all_documents = []
        try:
            for doc in rw.get_documents(params={"location": args.location}):
                all_documents.append(doc)
        except Exception as e:
            if all_documents:
                print(f"Warning: Error during pagination after {len(all_documents)} docs: {e}")
                print("Continuing with documents retrieved so far...")
            else:
                print(f"Warning: Error fetching from location '{args.location}': {e}")
                if args.verbose:
                    import traceback
                    traceback.print_exc()

        if args.verbose:
            print(f"Received {len(all_documents)} documents from API")

        # Filter by tag locally
        filtered = [
            d for d in all_documents
            if hasattr(d, 'tags') and d.tags and args.tag in d.tags
        ]

        if args.verbose:
            print(f"After tag filter ('{args.tag}'): {len(filtered)} documents")

        # Skip documents already in archive
        to_archive = [
            d for d in filtered
            if not (hasattr(d, 'location') and d.location == 'archive')
        ]

        already_archived = len(filtered) - len(to_archive)
        if already_archived > 0:
            print(f"Skipping {already_archived} documents already in archive")

        if args.verbose:
            print(f"\nDocuments to archive: {len(to_archive)}\n")

        if not to_archive:
            print("No documents to archive.")
            return

        # Process documents
        success_count = 0
        error_count = 0

        for i, d in enumerate(to_archive, 1):
            title = d.title if hasattr(d, 'title') else 'N/A'
            category = d.category if hasattr(d, 'category') else 'N/A'

            if args.verbose or args.dry_run:
                print(f"[{i}/{len(to_archive)}] {title}")
                print(f"  Category: {category}")
                print(f"  Location: {d.location if hasattr(d, 'location') else 'N/A'}")

            if not args.dry_run:
                if archive_document(d.id, READWISE_TOKEN):
                    success_count += 1
                    if args.verbose:
                        print("  Status: Archived successfully")
                else:
                    error_count += 1
                    print(f"  Status: Failed to archive")

            if args.verbose or args.dry_run:
                print()

        # Summary
        if args.dry_run:
            print(f"\nDry run complete: {len(to_archive)} documents would be archived")
        else:
            print(f"\nArchived {success_count} documents")
            if error_count > 0:
                print(f"Failed to archive {error_count} documents")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
