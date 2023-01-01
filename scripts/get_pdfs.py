"""

Get PDFs for all papers in `papers.bib`

"""

from typing import List, Dict
import re
import os
from scripts.sort_bib import get_bib_chunks
import requests
from collections import defaultdict


def get_bib_id(line: str) -> str:
    return re.search(r'@.*{(.*),', line).group(1)


def get_arxiv_id(line: str) -> str:
    return re.search(r'arxiv.*=.*({|\")(.+)(}|\")', line).group(2)


def bib_title(line: str) -> str:
    line = line.replace('{', '').replace('}', '').replace('"', '')
    return re.search(r'title.*=(.*),', line).group(1).strip()


def create_all_slugs(titles: List[str]) -> List[str]:
    """This fucntion needs to apply to the entire dataframe because we need
    to guarantee uniqueness of slugs"""

    assert len(set(titles)) == len(titles), "Doesnt work if titles arent unique."

    from slugify import slugify as _slugify

    def slugify(s: str) -> str:
        # As we know in the current state of the project,
        # the slug function in webflow will remove the "'".
        # However this list might extend in the future along the project.
        return _slugify(s, replacements=[("'", "")])

    starting_slugs = [slugify(s=title) for title in titles]

    # map between slug & title
    slug_to_titles = defaultdict(list)
    for title, slug in zip(titles, starting_slugs):
        slug_to_titles[slug].append(title)

    # build, while resolving conflicts
    final_slugs = []
    for title, slug in zip(titles, starting_slugs):
        competing_titles = slug_to_titles[slug]
        if len(competing_titles) == 1:  # itself, no competitor
            final_slugs.append(slug)
        else:
            pos = competing_titles.index(title)
            final_slugs.append(f"{slug}-{pos}")

    return final_slugs


if __name__ == '__main__':
    # 1) read
    with open('_bibliography/papers.bib') as f_in:
        lines = f_in.readlines()

    # 2) organize
    bib_chunks: List[str] = get_bib_chunks(lines=lines)

    # 3) get slugs first
    titles = []
    for bib_chunk in bib_chunks:
        title_line = [line.strip() for line in bib_chunk.split('\n')
                      if line.strip().startswith('title')][0]
        titles.append(bib_title(line=title_line))

    slugs = create_all_slugs(titles=titles)
    assert len(slugs) == len(bib_chunks)

    # 4) figure out URLs to fetch PDFs
    slug_to_metadata: Dict = {}
    for slug, bib_chunk in zip(slugs, bib_chunks):

        # start w/ arxiv papers
        arxiv_lines = [line for line in bib_chunk.split('\n') if 'arxiv' in line]
        if arxiv_lines:
            arxiv_id = get_arxiv_id(line=arxiv_lines[0])
            target_pdf_path = os.path.join('assets/pdf/', f'{slug}.pdf')
            if not os.path.exists(target_pdf_path):
                requests.request()

                month_score = \
                [score for month, score in month_to_score.items() if month in month_line][
                    0]
                year_line = [line.lower() for line in bib_chunk.split('\n') if 'year' in line][0]
                year_score = get_year(year_line=year_line)
                score = year_score * 100 + month_score
                bib_chunks_with_scores.append((bib_chunk, score))

            sorted_bib_chunks_with_scores = sorted(bib_chunks_with_scores,
                                                   key=lambda tup: tup[-1],
                                                   reverse=True)
