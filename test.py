from reportlab.pdfbase import pdfmetrics
from pprint import pprint

import io

widths = {}
ratios = []

for i in range(1, 100):
    width = pdfmetrics.stringWidth("Preliminary", "Courier", i)
    widths[i] = width
    ratios.append(width / i)

# pprint(ratios)
pprint(widths)