# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests",
#     "python-slugify",
# ]
# ///
"""

Get PDFs for all papers in `papers.bib`

"""

import os
import re
from collections import defaultdict
from time import sleep
from typing import Dict, List

import requests


def get_bib_chunks(lines: List[str]) -> List[str]:
    # get bib starts
    index_starts = []
    for i, line in enumerate(lines):
        if line.startswith('@'):
            index_starts.append(i)
    # group bibs
    bibs = []
    for i in range(len(index_starts) - 1):
        start = index_starts[i]
        end = index_starts[i + 1]
        bibs.append(''.join(lines[start: end]))
    # get last bib too
    bibs.append(''.join(lines[index_starts[-1]:]))
    return bibs


def get_bib_id(line: str) -> str:
    return re.search(r'@.*{(.*),', line).group(1)


def get_arxiv_id(line: str) -> str:
    return re.search(r'arxiv.*=.*({|\")(.+)(}|\")', line).group(2)


def get_acl_id(line: str) -> str:
    return re.search(r'acl.*=.*({|\")(.+)(}|\")', line).group(2)


def get_or_id(line: str) -> str:
    return re.search(r'openreview.*=.*({|\")(.+)(}|\")', line).group(2)


def get_pmc_id(line: str) -> str:
    return re.search(r'pmc.*=.*({|\")(.+)(}|\")', line).group(2)


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


def fetch_arxiv_pdf(arxiv_id: str, target_path: str):
    USER_AGENT = "Kyle Lo, for personal research website <kylel@allenai.org>"
    URL_PREFIX = "https://export.arxiv.org/pdf/"
    uri = URL_PREFIX + arxiv_id
    response = requests.get(uri, headers={"User-Agent": USER_AGENT})
    if response.ok:
        with open(target_path, "wb") as f_out:
            f_out.write(response.content)


def fetch_acl_pdf(acl_id: str, target_path: str):
    USER_AGENT = "Kyle Lo, for personal research website <kylel@allenai.org>"
    URL_PREFIX = "https://aclanthology.org/"
    uri = URL_PREFIX + acl_id + '.pdf'
    response = requests.get(uri, headers={"User-Agent": USER_AGENT})
    if response.ok:
        with open(target_path, "wb") as f_out:
            f_out.write(response.content)


def fetch_openreview_pdf(openreview_id: str, target_path: str):
    USER_AGENT = "Kyle Lo, for personal research website <kylel@allenai.org>"
    URL_PREFIX = "https://openreview.net/pdf?id="
    uri = URL_PREFIX + openreview_id
    response = requests.get(uri, headers={"User-Agent": USER_AGENT})
    if response.ok:
        with open(target_path, "wb") as f_out:
            f_out.write(response.content)


def fetch_pmc_pdf(pmc_id: str, target_path: str):
    USER_AGENT = "Kyle Lo, for personal research website <kylel@allenai.org>"
    URL_PREFIX = "https://www.ncbi.nlm.nih.gov/pmc/articles/"
    uri = URL_PREFIX + pmc_id + '/pdf/'
    response = requests.get(uri, headers={"User-Agent": USER_AGENT})
    if response.ok:
        with open(target_path, "wb") as f_out:
            f_out.write(response.content)


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

    # 4) fetch any arXiv PDFs first
    bib_id_to_slug: Dict = {}
    for slug, bib_chunk in zip(slugs, bib_chunks):

        print('pdf={' + slug + '.pdf}')

        # bib id
        bib_id_lines = [line for line in bib_chunk.split('\n') if line.strip().startswith('@')]
        assert len(bib_id_lines) == 1
        bib_id = get_bib_id(line=bib_id_lines[0])
        bib_id_to_slug[bib_id] = slug

        # pdf path
        target_pdf_path = os.path.join('assets/pdf/', f'{slug}.pdf')

        # start w/ arxiv papers
        arxiv_lines = [line for line in bib_chunk.split('\n') if line.strip().startswith('arxiv')]
        if arxiv_lines:
            assert len(arxiv_lines) == 1
            arxiv_id = get_arxiv_id(line=arxiv_lines[0])
            # download
            if not os.path.exists(target_pdf_path):
                fetch_arxiv_pdf(arxiv_id=arxiv_id, target_path=target_pdf_path)
                sleep(2)

        # next ACL papers
        acl_lines = [line for line in bib_chunk.split('\n') if line.strip().startswith('acl')]
        if acl_lines:
            assert len(acl_lines) == 1
            acl_id = get_acl_id(line=acl_lines[0])
            # download
            if not os.path.exists(target_pdf_path):
                fetch_acl_pdf(acl_id=acl_id, target_path=target_pdf_path)
                sleep(2)

        # next OpenReview papers
        or_lines = [line for line in bib_chunk.split('\n') if line.strip().startswith('openreview')]
        if or_lines:
            assert len(or_lines) == 1
            openreview_id = get_or_id(line=or_lines[0])
            # download

            if not os.path.exists(target_pdf_path):
                fetch_openreview_pdf(openreview_id=openreview_id, target_path=target_pdf_path)
                sleep(2)

        # fetch any pubmed central papers
        pmc_lines = [line for line in bib_chunk.split('\n') if line.strip().startswith('pmc')]
        if pmc_lines:
            assert len(pmc_lines) == 1
            pmc_id = get_pmc_id(line=pmc_lines[0])
            # download
            if not os.path.exists(target_pdf_path):
                fetch_pmc_pdf(pmc_id=pmc_id, target_path=target_pdf_path)
                sleep(2)

        # print anything else here, so manually add those PDFs
        if not os.path.exists(target_pdf_path):
            print(f'Missing; {slug}.pdf')

