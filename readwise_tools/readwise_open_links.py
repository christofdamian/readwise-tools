#!/usr/bin/env python3

import webbrowser
import os
from dotenv import load_dotenv
from readwise import ReadwiseReader
import argparse
import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

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

documents = rw.get_documents(params={"location": "later", "tag": tag_to_filter})

for d in documents:
    webbrowser.get("firefox").open_new_tab(d.source_url)
