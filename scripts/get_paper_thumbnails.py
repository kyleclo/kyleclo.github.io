"""

Thumbnails of every paper we have PDF

"""

import os
from glob import glob

from mmda.rasterizers import PDF2ImageRasterizer
from tqdm import tqdm

pdf_dir = 'assets/pdf/'
thumbnail_dir = 'assets/img/publication_preview/'

rasterizer = PDF2ImageRasterizer()

for pdfname in tqdm(os.listdir(pdf_dir)):
    pngfile = os.path.join(thumbnail_dir, pdfname.replace('.pdf', '.png'))
    if os.path.exists(pngfile):
        continue

    pdffile = os.path.join(pdf_dir, pdfname)
    pdfimages = rasterizer.rasterize(input_pdf_path=pdffile, dpi=72)
    first_page_img = pdfimages[0]

    with open(pngfile, 'wb') as f_out:
        first_page_img.save(f_out, format='png')

