#!/usr/bin/env python3
"""
Readwise to Todoist Sync Tool

Syncs Readwise Reader documents tagged with 'todoist' to Todoist as tasks.

Setup:
1. Add READWISE_TOKEN and TODOIST_TOKEN to your .env file
2. Tag documents in Readwise Reader with 'todoist' tag
3. Run: readwise-to-todoist

The tool tracks already processed documents to avoid duplicates.
"""

import os
from dotenv import load_dotenv
from readwise import ReadwiseReader
from todoist_api_python.api import TodoistAPI

load_dotenv()

READWISE_TOKEN = os.getenv("READWISE_TOKEN")
TODOIST_TOKEN = os.getenv("TODOIST_TOKEN")
STATE_FILE = os.path.expanduser("~/.readwise_todoist_transferred")


def load_transferred_highlights():
    try:
        with open(STATE_FILE, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()


def append_transferred_highlight(highlight_id):
    with open(STATE_FILE, 'a') as f:
        f.write(str(highlight_id) + '\n')


def get_readwise_documents_with_todoist_tag(readwise_client):
    try:
        documents = readwise_client.get_documents(
            params={
                "tag": "todoist"
            }
        )
        return list(documents)
    except Exception as e:
        print(f"Error fetching documents with todoist tag: {e}")
        return []


def create_todoist_task(document, todoist_api):
    # Handle case where title might be None
    title = getattr(document, 'title', None) or "Untitled Document"
    task_content = title[:500]
    if len(title) > 500:
        task_content += "..."

    description_parts = []
    summary = getattr(document, 'summary', None)
    if summary:
        description_parts.append(f"Summary: {summary}")
    
    author = getattr(document, 'author', None)
    if author:
        description_parts.append(f"Author: {author}")
    
    source_url = getattr(document, 'source_url', None) or getattr(document, 'url', None)
    if source_url:
        description_parts.append(f"URL: {source_url}")

    description = "\n".join(description_parts) if description_parts else ""

    try:
        task = todoist_api.add_task(
            content=task_content,
            description=description,
            labels=["readwise", "reader"],
            due_string="today"
        )
        return task
    except Exception as e:
        print(f"Failed to create Todoist task: {e}")
        return None


def main():
    if not (READWISE_TOKEN and TODOIST_TOKEN):
        print("Missing environment variables. Check your .env file.")
        print("Required: READWISE_TOKEN, TODOIST_TOKEN")
        return

    try:
        readwise_client = ReadwiseReader(token=READWISE_TOKEN)
        todoist_api = TodoistAPI(TODOIST_TOKEN)
        transferred_ids = load_transferred_highlights()

        print("Fetching Readwise documents tagged with 'todoist'...")
        documents = get_readwise_documents_with_todoist_tag(readwise_client)

        if not documents:
            print("No documents found with 'todoist' tag.")
            return

        new_transfers = 0
        for document in documents:
            document_id = str(getattr(document, 'id', 'unknown'))
            if document_id not in transferred_ids:
                title = getattr(document, 'title', None) or "Untitled Document"
                print(f"Creating Todoist task from: {title[:100]}...")
                task = create_todoist_task(document, todoist_api)

                if task:
                    append_transferred_highlight(document_id)
                    new_transfers += 1
                    print(f"✓ Task created: {task.content}")
                else:
                    print(f"✗ Failed to create task for document {document_id}")
            else:
                title = getattr(document, 'title', None) or "Untitled Document"
                print(f"Skipping already transferred document: {title[:50]}...")

        print(f"Transferred {new_transfers} new documents to Todoist. Total tracked: {len(transferred_ids) + new_transfers}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
