"""

Sort news articles

python scripts/sort_news_articles.py _news/

"""

import argparse
import os
import shutil
from datetime import datetime

import dateutil.parser


def parse_date(content):
    for line in content.split("\n"):
        if line.strip().startswith("date:"):
            try:
                date_str = line.split("date:", 1)[1].strip()
                return dateutil.parser.parse(date_str)
            except ValueError:
                return None
    return None


def sort_and_renumber_articles(directory):
    # Get all announcement files in the directory
    files = [
        f
        for f in os.listdir(directory)
        if f.endswith(".md") and not f.startswith("TEMPLATE")
    ]

    # Read dates and sort files
    file_dates = []
    for filename in files:
        with open(os.path.join(directory, filename), "r") as f:
            content = f.read()
            date = parse_date(content)
            if date:
                file_dates.append((filename, date))
            else:
                print(f"Warning: Couldn't parse date in {filename}")

    # Sort files based on their dates
    file_dates.sort(key=lambda x: x[1])

    # First stage: Rename to staging files
    staging_files = []
    for i, (old_filename, _) in enumerate(file_dates, start=1):
        old_path = os.path.join(directory, old_filename)
        staging_filename = f"staging_{i:03d}.md"
        staging_path = os.path.join(directory, staging_filename)
        shutil.move(old_path, staging_path)
        staging_files.append(staging_path)
        print(f"Staged {old_filename} as {staging_filename}")

    # Second stage: Rename to final announcement files
    for i, staging_path in enumerate(staging_files, start=1):
        final_filename = f"announcement_{i:03d}.md"
        final_path = os.path.join(directory, final_filename)
        shutil.move(staging_path, final_path)
        print(f"Renamed staging file to {final_filename}")


def main():
    parser = argparse.ArgumentParser(
        description="Sort articles by date and renumber them safely using two-stage renaming."
    )
    parser.add_argument(
        "directory", help="Path to the directory containing the announcement files"
    )

    args = parser.parse_args()

    sort_and_renumber_articles(args.directory)


if __name__ == "__main__":
    main()
