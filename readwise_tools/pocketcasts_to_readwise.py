#!/usr/bin/env python3

from pycketcasts import PocketCast
from readwise import ReadwiseReader
from dotenv import load_dotenv
import os

load_dotenv()

POCKETCASTS_EMAIL = os.getenv("POCKETCASTS_EMAIL")
POCKETCASTS_PASSWORD = os.getenv("POCKETCASTS_PASSWORD")
READWISE_TOKEN = os.getenv("READWISE_TOKEN")
STATE_FILE = os.path.expanduser("~/.pocketcasts_transferred")


def load_transferred_episodes():
    try:
        with open(STATE_FILE, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()

def append_transferred_episode(uuid):
    with open(STATE_FILE, 'a') as f:
        f.write(uuid + '\n')

def get_starred_episodes():
    client = PocketCast(email=POCKETCASTS_EMAIL, password=POCKETCASTS_PASSWORD)
    return client.starred

def send_episode_to_readwise(episode, rw: ReadwiseReader):
    try:
        rw.create_document(
            url="https://pca.st/episode/" + episode.uuid,
            title=episode.title,
            summary=episode.show_notes,
            tags=[
                "podcast",
                "friday",
                "pocketcasts",
                "pocketcasts-to-readwise"
            ]
        )
        print(f"Saved to Readwise: {episode.title}")
    except Exception as e:
        print(f"Failed to save: {episode.title} – {e}")

def main():
    if not (POCKETCASTS_EMAIL and POCKETCASTS_PASSWORD and READWISE_TOKEN):
        print("Missing environment variables. Check your .env file.")
        return

    rw = ReadwiseReader(token=READWISE_TOKEN)
    transferred_uuids = load_transferred_episodes()
    episodes = get_starred_episodes()

    new_transfers = 0
    for ep in episodes:
        if ep.uuid not in transferred_uuids:
            send_episode_to_readwise(ep, rw)
            append_transferred_episode(ep.uuid)
            new_transfers += 1
        else:
            print(f"Skipping already transferred: {ep.title}")
    
    print(f"Transferred {new_transfers} new episodes. Total tracked: {len(transferred_uuids) + new_transfers}")


if __name__ == "__main__":
    main()
