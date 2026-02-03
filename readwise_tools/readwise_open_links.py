#!/usr/bin/env python3

import webbrowser
import os
from dotenv import load_dotenv
from readwise import ReadwiseReader
import argparse
import logging

load_dotenv()

READWISE_TOKEN = os.getenv("READWISE_TOKEN")
BROWSER = os.getenv("BROWSER", "firefox")


def main():
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)
    
    if not READWISE_TOKEN:
        print("Missing environment variables. Check your .env file.")
        print("Required: READWISE_TOKEN")
        return

    parser = argparse.ArgumentParser(
        description="Open Reader URLs in browser",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("-t", "--tag", help="tag to filter by", required=True)
    parser.add_argument("-d", "--dry-run", action="store_true", help="show what would be opened without opening browser tabs")
    parser.add_argument("-v", "--verbose", action="store_true", help="output detailed information for debugging")
    args = parser.parse_args()

    tag_to_filter = args.tag

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

        opened_count = 0
        for d in documents:
            if args.verbose:
                print(f"Document {opened_count + 1}:")
                print(f"  Title: {d.title if hasattr(d, 'title') else 'N/A'}")
                print(f"  URL: {d.source_url}")
                print(f"  Tags: {', '.join(d.tags) if hasattr(d, 'tags') and d.tags else 'None'}")
                print()

            if args.dry_run:
                if not args.verbose:
                    print(f"Would open: {d.source_url}")
            else:
                webbrowser.get(BROWSER).open_new_tab(d.source_url)
            opened_count += 1

        if args.dry_run:
            print(f"\nDry run: Found {opened_count} documents with tag '{tag_to_filter}' that would be opened")
        else:
            print(f"Opened {opened_count} documents with tag '{tag_to_filter}' in browser")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
