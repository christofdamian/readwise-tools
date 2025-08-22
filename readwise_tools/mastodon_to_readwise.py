#!/usr/bin/env python3

import requests
from readwise import ReadwiseReader
from dotenv import load_dotenv
import os
from urllib.parse import urljoin

load_dotenv()

MASTODON_INSTANCE = os.getenv("MASTODON_INSTANCE")
MASTODON_TOKEN = os.getenv("MASTODON_TOKEN")
READWISE_TOKEN = os.getenv("READWISE_TOKEN")
STATE_FILE = os.path.expanduser("~/.mastodon_transferred")


def load_transferred_bookmarks():
    try:
        with open(STATE_FILE, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()


def append_transferred_bookmark(status_id):
    with open(STATE_FILE, 'a') as f:
        f.write(status_id + '\n')


def get_mastodon_bookmarks():
    if not MASTODON_INSTANCE or not MASTODON_TOKEN:
        raise ValueError("MASTODON_INSTANCE and MASTODON_TOKEN must be set")
    
    bookmarks = []
    url = urljoin(MASTODON_INSTANCE, "/api/v1/bookmarks")
    headers = {"Authorization": f"Bearer {MASTODON_TOKEN}"}
    
    while url:
        response = requests.get(url, headers=headers, params={"limit": 40})
        response.raise_for_status()
        
        batch = response.json()
        bookmarks.extend(batch)
        
        # Handle pagination via Link header
        link_header = response.headers.get('Link', '')
        url = None
        if 'rel="next"' in link_header:
            for link in link_header.split(','):
                if 'rel="next"' in link:
                    url = link.split(';')[0].strip('<>')
                    break
    
    return bookmarks


def send_bookmark_to_readwise(status, rw: ReadwiseReader):
    try:
        # Extract content from status
        content = status.get('content', '')
        # Remove HTML tags for summary
        import re
        clean_content = re.sub(r'<[^>]+>', '', content)
        
        # Get the URL - prefer the original URL if it's a reblog
        url = status.get('url', '')
        if status.get('reblog'):
            url = status['reblog'].get('url', url)
        
        # Create title from account and content preview
        account = status.get('account', {})
        display_name = account.get('display_name') or account.get('username', 'Unknown')
        title_preview = clean_content[:100] + ("..." if len(clean_content) > 100 else "")
        title = f"{display_name}: {title_preview}" if title_preview else f"Post by {display_name}"
        
        rw.create_document(
            url=url,
            title=title,
            summary=clean_content,
            tags=[
                "mastodon",
                "bookmark",
                "social",
                "mastodon-to-readwise"
            ]
        )
        print(f"Saved to Readwise: {title}")
    except Exception as e:
        print(f"Failed to save bookmark: {e}")


def main():
    if not (MASTODON_INSTANCE and MASTODON_TOKEN and READWISE_TOKEN):
        print("Missing environment variables. Check your .env file.")
        print("Required: MASTODON_INSTANCE, MASTODON_TOKEN, READWISE_TOKEN")
        return

    try:
        rw = ReadwiseReader(token=READWISE_TOKEN)
        transferred_ids = load_transferred_bookmarks()
        bookmarks = get_mastodon_bookmarks()

        new_transfers = 0
        for bookmark in bookmarks:
            status_id = bookmark.get('id')
            if status_id not in transferred_ids:
                send_bookmark_to_readwise(bookmark, rw)
                append_transferred_bookmark(status_id)
                new_transfers += 1
            else:
                account = bookmark.get('account', {})
                display_name = account.get('display_name') or account.get('username', 'Unknown')
                print(f"Skipping already transferred bookmark from {display_name}")
        
        print(f"Transferred {new_transfers} new bookmarks. Total tracked: {len(transferred_ids) + new_transfers}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()