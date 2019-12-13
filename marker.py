from PyPDF2 import PdfFileWriter, PdfFileReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.pagesizes import letter

import glob
import math
import io
from json import dumps

text_color = (0.5, 0.5, 0.5)
text_opacity = 0.3
text_font = "Helvetica"
text_scale = 0.9

def mark_pdf(src_filename, out_filename, text, *, only_first_page=False, cache=True):
    global text_color
    global text_opacity
    existing_pdf = PdfFileReader(open(src_filename, "rb"))

    output = PdfFileWriter()

    wmark_cache = {}

    for i in range(1 if only_first_page else existing_pdf.getNumPages()):

        page = existing_pdf.getPage(i)

        pagesize = [float(e) for e in page.mediaBox[2:]]
        cache_key = dumps(pagesize)

        wmark_pdf = wmark_cache[cache_key] if cache_key in wmark_cache.keys() else None
        
        if wmark_pdf is None:
            print(f"Creating new PDF for {cache_key}")
            text_lines = text.splitlines(False)
            test_width = max([stringWidth(line, text_font, 1) for line in text_lines])
            test_ratio = test_width / len(text_lines)
            textsize = math.sqrt(((pagesize[0] * text_scale)**2 + (pagesize[1] * text_scale)**2)) / (test_ratio + 1) / len(text_lines)
            text_width = stringWidth(text, text_font, textsize)

            packet = io.BytesIO()
            angle = math.atan2(*pagesize)
            can = canvas.Canvas(packet, pagesize=pagesize)
            can.setFont(text_font, textsize)
            can.setFillColorRGB(*text_color, text_opacity)
            can.translate(pagesize[0]/2 + textsize/4, pagesize[1]/2)
            can.rotate(90 - math.degrees(angle))

            i = -(len(text_lines) - 1) / 2
            for line in text_lines:
                can.drawCentredString(0, -textsize * i, line)
                i += 1

            can.save()
            packet.seek(0)
            wmark_pdf = PdfFileReader(packet)
            wmark_cache[cache_key] = wmark_pdf

        page.mergePage(wmark_pdf.getPage(0))
        output.addPage(page)

    outputStream = open(out_filename, "wb")
    output.write(outputStream)
    outputStream.close()

if __name__ == "__main__":
    mark_pdf("sample.pdf", "sample_marked.pdf", "Preliminary")
    