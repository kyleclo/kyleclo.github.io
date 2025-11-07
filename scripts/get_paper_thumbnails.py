# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pdf2image",
#     "tqdm",
# ]
# ///
"""

Thumbnails of every paper we have PDF

Requires poppler to be installed:
  macOS: brew install poppler
  Ubuntu: apt-get install poppler-utils

"""

import os
from pdf2image import convert_from_path
from tqdm import tqdm

pdf_dir = 'assets/pdf/'
thumbnail_dir = 'assets/img/publication_preview/'

for pdfname in tqdm(os.listdir(pdf_dir)):
    if not pdfname.endswith('.pdf'):
        continue

    pngfile = os.path.join(thumbnail_dir, pdfname.replace('.pdf', '.png'))
    if os.path.exists(pngfile):
        continue

    pdffile = os.path.join(pdf_dir, pdfname)

    try:
        # Convert first page of PDF to image
        images = convert_from_path(pdffile, first_page=1, last_page=1, dpi=72)
        if images:
            first_page_img = images[0]
            first_page_img.save(pngfile, format='PNG')
    except Exception as e:
        print(f"Error processing {pdfname}: {e}")

