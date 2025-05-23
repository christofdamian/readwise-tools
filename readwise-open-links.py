import webbrowser
import os
from dotenv import load_dotenv
from readwise import ReadwiseReader
from datetime import datetime, timedelta
from itertools import islice
import argparse

load_dotenv()
READWISE_TOKEN = os.getenv("READWISE_TOKEN")

parser = argparse.ArgumentParser(
    description="Open Reader URLs in browser",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("-t", "--tag",  help="tag to filter by",  required=True)
args = parser.parse_args()

tag_to_filter = args.tag


rw = ReadwiseReader(token=READWISE_TOKEN)

documents = rw.get_documents(
    params={
        "location": "archive",
        "updatedAfter": (datetime.now() - timedelta(days=14)).isoformat(),
    })

for d in islice(documents, 0, 100):
    if tag_to_filter in d.tags.keys():
        webbrowser.get("firefox").open_new_tab(d.source_url)
