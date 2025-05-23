from pycketcasts import PocketCast
from readwise import ReadwiseReader
from dotenv import load_dotenv
import os

load_dotenv()

POCKETCASTS_EMAIL = os.getenv("POCKETCASTS_EMAIL")
POCKETCASTS_PASSWORD = os.getenv("POCKETCASTS_PASSWORD")
READWISE_TOKEN = os.getenv("READWISE_TOKEN")


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

    episodes = get_starred_episodes()

    for ep in episodes:
        send_episode_to_readwise(ep, rw)


if __name__ == "__main__":
    main()
