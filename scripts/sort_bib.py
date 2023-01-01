"""

Sorts bib entries in reverse chronological order

"""

from typing import List, Tuple
import re


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


month_to_score = {
    'jan': 0,
    'feb': 1,
    'mar': 2,
    'apr': 3,
    'may': 4,
    'jun': 5,
    'jul': 6,
    'aug': 7,
    'sep': 8,
    'oct': 9,
    'nov': 10,
    'dec': 11
}


def get_year(year_line: str) -> int:
    return int(re.search(r'[0-9]{4}', year_line).group(0))


if __name__ == '__main__':
    # 1) read
    with open('_bibliography/papers.bib') as f_in:
        lines = f_in.readlines()

    # 2) organize
    bib_chunks: List[str] = get_bib_chunks(lines=lines)

    # 3) sort by date
    bib_chunks_with_scores: List[Tuple] = []
    for bib_chunk in bib_chunks:
        assert 'year' in bib_chunk
        assert 'month' in bib_chunk
        month_line = [line.lower() for line in bib_chunk.split('\n') if 'month' in line][0]
        month_score = [score for month, score in month_to_score.items() if month in month_line][0]
        year_line = [line.lower() for line in bib_chunk.split('\n') if 'year' in line][0]
        year_score = get_year(year_line=year_line)
        score = year_score * 100 + month_score
        bib_chunks_with_scores.append((bib_chunk, score))

    sorted_bib_chunks_with_scores = sorted(bib_chunks_with_scores,
                                           key=lambda tup: tup[-1],
                                           reverse=True)

    # 4) write
    with open('_bibliography/papers.bib', 'w') as f_out:
        f_out.write('---\n')
        f_out.write('---\n\n')
        for bib_chunk, _ in sorted_bib_chunks_with_scores:
            f_out.write(bib_chunk)
