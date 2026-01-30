#!/usr/bin/env python3
"""
Tags documents matching filter criteria in Readwise Reader.

Example usage:
    # Tag all articles and RSS items in 'later' with 'review'
    readwise-tag-filter --location later --category article --category rss --add-tag review

    # Dry run to see what would be tagged
    readwise-tag-filter --location later --category video --add-tag watch --dry-run
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


def update_document_tags(document_id: str, tags: list[str], token: str) -> bool:
    """Update a document's tags via the Readwise API."""
    url = f"{READWISE_API_BASE}/update/{document_id}/"
    headers = {"Authorization": f"Token {token}"}
    payload = {"tags": tags}

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
        description="Tag documents matching filter criteria",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-l", "--location",
        help="filter by location (new, later, archive, feed, shortlist)",
        default="later"
    )
    parser.add_argument(
        "-c", "--category",
        action="append",
        help="filter by category (can specify multiple: -c article -c rss -c video -c podcast)"
    )
    parser.add_argument(
        "--has-tag",
        help="filter by existing tag"
    )
    parser.add_argument(
        "-t", "--add-tag",
        help="tag to add to matching documents",
        required=True
    )
    parser.add_argument(
        "-d", "--dry-run",
        action="store_true",
        help="show what would be tagged without making changes"
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
        print(f"  Location: {args.location}")
        print(f"  Categories: {args.category if args.category else 'all'}")
        print(f"  Has tag: {args.has_tag if args.has_tag else 'any'}")
        print(f"  Add tag: {args.add_tag}")
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
            else:
                raise

        if args.verbose:
            print(f"Received {len(all_documents)} documents from API")

        # Filter by category locally (API category filter is buggy)
        if args.category:
            filtered = [
                d for d in all_documents
                if hasattr(d, 'category') and d.category in args.category
            ]
            if args.verbose:
                print(f"After category filter ({', '.join(args.category)}): {len(filtered)} documents")
        else:
            filtered = all_documents

        # Filter by existing tag if specified
        if args.has_tag:
            filtered = [
                d for d in filtered
                if hasattr(d, 'tags') and d.tags and args.has_tag in d.tags
            ]
            if args.verbose:
                print(f"After tag filter (has '{args.has_tag}'): {len(filtered)} documents")

        # Skip documents that already have the target tag
        to_tag = [
            d for d in filtered
            if not (hasattr(d, 'tags') and d.tags and args.add_tag in d.tags)
        ]

        already_tagged = len(filtered) - len(to_tag)
        if already_tagged > 0:
            print(f"Skipping {already_tagged} documents that already have tag '{args.add_tag}'")

        if args.verbose:
            print(f"\nDocuments to tag: {len(to_tag)}\n")

        if not to_tag:
            print("No documents to tag.")
            return

        # Process documents
        success_count = 0
        error_count = 0

        for i, d in enumerate(to_tag, 1):
            title = d.title if hasattr(d, 'title') else 'N/A'
            category = d.category if hasattr(d, 'category') else 'N/A'

            # Merge existing tags with new tag
            existing_tags = list(d.tags.keys()) if hasattr(d, 'tags') and d.tags else []
            new_tags = existing_tags + [args.add_tag]

            if args.verbose or args.dry_run:
                print(f"[{i}/{len(to_tag)}] {title}")
                print(f"  Category: {category}")
                print(f"  Current tags: {', '.join(existing_tags) if existing_tags else 'none'}")
                print(f"  New tags: {', '.join(new_tags)}")

            if not args.dry_run:
                if update_document_tags(d.id, new_tags, READWISE_TOKEN):
                    success_count += 1
                    if args.verbose:
                        print("  Status: Tagged successfully")
                else:
                    error_count += 1
                    print(f"  Status: Failed to tag")

            if args.verbose or args.dry_run:
                print()

        # Summary
        if args.dry_run:
            print(f"\nDry run complete: {len(to_tag)} documents would be tagged with '{args.add_tag}'")
        else:
            print(f"\nTagged {success_count} documents with '{args.add_tag}'")
            if error_count > 0:
                print(f"Failed to tag {error_count} documents")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
