#!/usr/bin/env python3

import webbrowser
import os
from dotenv import load_dotenv
from readwise import ReadwiseReader
import argparse
import logging

load_dotenv()

READWISE_TOKEN = os.getenv("READWISE_TOKEN")


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
    args = parser.parse_args()

    tag_to_filter = args.tag
    
    try:
        rw = ReadwiseReader(token=READWISE_TOKEN)
        documents = rw.get_documents(params={"location": "later", "tag": tag_to_filter})

        opened_count = 0
        for d in documents:
            webbrowser.get("firefox").open_new_tab(d.source_url)
            opened_count += 1
        
        print(f"Opened {opened_count} documents with tag '{tag_to_filter}' in browser")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
