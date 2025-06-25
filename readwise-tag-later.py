#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from readwise import ReadwiseReader
import argparse

load_dotenv()
READWISE_TOKEN = os.getenv("READWISE_TOKEN")

parser = argparse.ArgumentParser(
    description="Tag all items in later",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("-t", "--tag",  help="tag to use",  required=True)
args = parser.parse_args()

tag_to_filter = args.tag


rw = ReadwiseReader(token=READWISE_TOKEN)

documents = rw.get_documents(
    params={
        "location": "later",
    })

for d in documents:
    print(d.title)
