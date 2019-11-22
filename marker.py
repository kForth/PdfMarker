from PyPDF2 import PdfFileWriter, PdfFileReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

import glob
import math
import io

text_color = (0.5, 0.5, 0.5)
text_opacity = 0.3
text_font = "Courier"

def mark_pdf(src_filename, out_filename, text, *, only_first_page=False):
    global text_color
    global text_opacity
    existing_pdf = PdfFileReader(open(src_filename, "rb"))

    output = PdfFileWriter()

    for i in range(1 if only_first_page else existing_pdf.getNumPages()):
        textsize = 150  # TODO: Set this dynamically somehow
        page = existing_pdf.getPage(0)
        pagesize = [float(e) for e in page.mediaBox[2:]]
        packet = io.BytesIO()
        angle = math.atan2(*pagesize)
        can = canvas.Canvas(packet, pagesize=pagesize)
        can.setFont(text_font, textsize)
        can.setFillColorRGB(*text_color, text_opacity)
        can.translate(pagesize[0]/2 + textsize/4, pagesize[1]/2)
        can.rotate(90 - math.degrees(angle))
        can.drawCentredString(0, 0, text)
        can.save()
        packet.seek(0)
        new_pdf = PdfFileReader(packet)

        page.mergePage(new_pdf.getPage(0))
        output.addPage(page)

    outputStream = open(out_filename, "wb")
    output.write(outputStream)
    outputStream.close()

if __name__ == "__main__":
    mark_pdf("pdfs/sample.pdf", "sample_marked.pdf", "Preliminary")
    