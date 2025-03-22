"""

Scrape Google Scholar for a given author and save to a JSONL file.

Call:
    python scripts/scrape_google_scholar.py

"""

import json
import os
import time
from datetime import datetime

from scholarly import scholarly
from tqdm import tqdm

TODAY = datetime.today().strftime("%Y-%m-%d")
MY_SCHOLAR_ID = "VJS12uMAAAAJ"
OUTPUT_FILE = f"_bibliography/gscholar_export_{TODAY}.jsonl"


if __name__ == "__main__":
    # Fetch author using ID
    author = scholarly.search_author_id(MY_SCHOLAR_ID)
    author = scholarly.fill(author)
    print(f"Processing publications for: {author['name']}")
    print(f"Total publications found: {len(author['publications'])}")

    # Get all info per publication
    pubs = []
    for i, pub in tqdm(enumerate(author["publications"])):
        time.sleep(1)  # Avoid rate-limiting

        pub_filled = scholarly.fill(pub)
        pubs.append(pub_filled)
        print(
            f"Processing publication {i + 1}/{len(author['publications'])}: {pub_filled['bib']['title']}"
        )

    # Save to JSONL file
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        for pub in pubs:
            json.dump(pub, f)
            f.write("\n")
    print(f"Total publications processed: {len(pubs)} and saved to {OUTPUT_FILE}")
