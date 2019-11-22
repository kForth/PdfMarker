from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QColorDialog, QFontDialog
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QColor, QPixmap, QPainter
from reportlab.pdfgen import canvas
from reportlab.lib import pagesizes, units

import marker

import tempfile
import glob
import io
import os

from py_mainwindow import Ui_MainWindow

class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        # uic.loadUi('mainwindow.ui', self)
        self.setupUi = Ui_MainWindow.setupUi
        self.retranslateUi = lambda e: Ui_MainWindow.retranslateUi(self, e)
        self.setupUi(self, self)

        self.single_tab_height = 132
        self.multi_tab_height = 227
        self.tab_height_diff = abs(self.multi_tab_height - self.single_tab_height)

        self.previewPixmap = QPixmap(QSize(0, 0))

        self.resizeEvent = lambda e: self.update_preview()

        self.tabWidget.currentChanged.connect(self.updateTab)

        self.watermarkTxtBox.setPlainText("Preliminary")  # TODO: Set text from config

        self.previewPagesizeDropdown.addItem("From File")
        self.pagesizes = {}
        unit_dict = {
            units.inch: '"',
            units.cm: 'cm',
            units.mm: 'mm',
            units.pica: 'p'
        }
        for elem in reversed(dir(pagesizes)):
            if ord(elem[0]) >= ord('A') and ord(elem[0]) <= ord('Z'):
                psize = getattr(pagesizes, elem)
                elem_str = elem.title().replace('_', ' ')
                if psize is pagesizes.ELEVENSEVENTEEN:
                    elem_str = "Eleven Seventeen"
                # TODO: Config file to pick what units are shown
                for unit, symbol in list(unit_dict.items())[:2]:
                    w = round(psize[0] / unit, 2)
                    h = round(psize[1] / unit, 2)
                    elem_str += f" ({w}{symbol} x {h}{symbol})"
                self.pagesizes[elem_str] = psize
                self.previewPagesizeDropdown.addItem(elem_str)
        self.previewPagesizeDropdown.currentTextChanged.connect(self.update_preview_page)
        self.previewOrientationDropdown.currentTextChanged.connect(self.update_preview_page)

        self.fontDropdown.clear()
        for font in canvas.Canvas(io.BytesIO()).getAvailableFonts():
            self.fontDropdown.addItem(font)
        self.fontDropdown.currentTextChanged.connect(self.handle_font_dropdown_change)
        # TODO: Set font from config

        self.watermark_color_label_style = "QWidget {{ border: 1px solid #000; background-color: {0}}}"
        self.selectColorBtn.clicked.connect(self.handle_select_color_btn)
        self.set_watermark_color(color=QColor.fromRgb(*[int(e * 255) for e in marker.text_color]), opacity=marker.text_opacity)
        self.opacitySlider.setValue(int(marker.text_opacity * 100))
        # TODO: Set color and opacity from config
        self.opacitySlider.valueChanged.connect(self.handle_opacity_slider_change)

        ## Single PDF
        self.singleSrcFileTxtBox.returnPressed.connect(lambda: self.update_preview())
        self.singleOverwriteBtn.clicked.connect(self.handle_single_overwrite)
        self.singleSaveAsBtn.clicked.connect(self.handle_single_save_as)
        self.singleSelectSrcBtn.clicked.connect(self.handle_select_single_src_file)

        ## Batch PDF
        self.selectSrcDirBtn.clicked.connect(self.handle_batch_select_src_dir_btn)
        self.quickSrcDirBtn.clicked.connect(self.handle_quick_select_src_dir_btn)
        self.selectOutDirBtn.clicked.connect(self.handle_batch_select_out_dir_btn)
        self.quickOutDirBtn.clicked.connect(self.handle_quick_select_out_dir_btn)
        self.batchPreviewBtn.clicked.connect(self.handle_batch_preview_btn)
        self.goBtn.clicked.connect(self.batch_add_watermark)

        self.resize(1, 1)
        self.tabWidget.setCurrentIndex(1)  # TODO: From last session?
        self.updateTab(1)
        self.show()
        self.update_preview_page()

    def update_preview_page(self):
        size = self.previewPagesizeDropdown.currentText()
        orientation = self.previewOrientationDropdown.currentText()
        psize = pagesizes.letter
        if size == "From File":
            psize = pagesizes.letter
            self.previewOrientationDropdown.setEnabled(False)
        else:
            self.previewOrientationDropdown.setEnabled(True)
            psize = self.pagesizes[size]
        if orientation.lower() == "landscape":
            psize = psize[::-1]  
        self.update_preview()

    def set_watermark_font(self, font=None):
        if font is not None:
            marker.text_font = font
            self.update_preview()

    def set_watermark_color(self, *, color=None, opacity=None):
        if color is not None:
            self.colorLabel.setStyleSheet(self.watermark_color_label_style.format(color.name()))
            marker.text_color = [e/255.0 for e in color.getRgb()[:3]]
        if opacity is not None:
            marker.text_opacity = opacity
        self.update_preview()

    def handle_font_dropdown_change(self, font):
        self.set_watermark_font(font)

    def handle_select_color_btn(self):
        dialog = QColorDialog(self)
        dialog.setWindowTitle("Select Text Color")
        dialog.colorSelected.connect(lambda c: self.set_watermark_color(color=c))
        dialog.show()
        
    def handle_opacity_slider_change(self, *, ignore=False):
        self.set_watermark_color(opacity=self.opacitySlider.value() / 100.0)

    def updateTab(self, tab):
        preview_height = int(self.height())
        if tab == 0:
            pass
            self.tabWidget.setFixedHeight(self.single_tab_height)
            self.setMinimumHeight(580 - self.tab_height_diff)
            preview_height -= self.tab_height_diff
        elif tab == 1:
            self.tabWidget.setFixedHeight(self.multi_tab_height)
            self.setMinimumHeight(580)
            preview_height += self.tab_height_diff
        self.update_preview()
        self.resize(self.width(), preview_height)

    def handle_select_single_src_file(self):
        filename = QFileDialog.getOpenFileName(self, 'Open PDF', '', '*.pdf, *.PDF')[0]
        if filename:
            self.single_src_filename = filename
            self.singleSrcFileTxtBox.setText(self.single_src_filename)
            self.update_preview()

    def handle_single_overwrite(self):
        self.setEnabled(False)
        text = self.watermarkTxtBox.toPlainText()
        if text: 
            if self.single_src_filename:
                marker.mark_pdf(self.single_src_filename, self.single_src_filename, text)
                self.show_msg_box("Done", "Done", "Saved as " + self.single_src_filename.split("/")[-1], buttons=QMessageBox.Ok)
        self.setEnabled(True)

    def handle_single_save_as(self):
        self.setEnabled(False)
        text = self.watermarkTxtBox.toPlainText()
        if text: 
            if self.single_src_filename: 
                out_filename = QFileDialog.getSaveFileName(self, 'Save PDF', self.single_src_filename, '*.pdf, *.PDF')[0]
                if out_filename:
                    marker.mark_pdf(self.single_src_filename, out_filename, text)
                    self.show_msg_box("Done", "Done", "Saved as " + out_filename.split("/")[-1], buttons=QMessageBox.Ok)
        self.setEnabled(True)

    def handle_quick_select_src_dir_btn(self):
        self.srcDirTextBox.setText(os.path.dirname(os.path.realpath(__file__)))

    def handle_quick_select_out_dir_btn(self):
        self.outDirTextBox.setText(os.path.dirname(os.path.realpath(__file__)))

    def handle_batch_select_src_dir_btn(self):
        new_dir = QFileDialog.getExistingDirectory(self, 'Source Directory')
        if new_dir:
            self.srcDirTextBox.setText(new_dir)

    def handle_batch_select_out_dir_btn(self):
        new_dir = QFileDialog.getExistingDirectory(self, 'Output Directory')
        if new_dir:
            self.outDirTextBox.setText(new_dir)

    def handle_batch_preview_btn(self):
        tempdir = tempfile.gettempdir()
        if self.srcDirTextBox.text():
            files = glob.glob(f'{self.srcDirTextBox.text()}/*.pdf')
            if files:
                out_file = f"{tempdir}/preview.pdf"
                marker.mark_pdf(files[0], f'{self.outDirTextBox.text()}/{out_file}', self.watermarkTxtBox.toPlainText(), only_first_page=True)
                os.system("open " + out_file)
            else:
                self.show_msg_box("Cannot find any PDFs.", "Error", icon=QMessageBox.Warning)
        else:
            self.show_msg_box("Invalid Source Directory.", "Error", icon=QMessageBox.Warning)
        print(tempdir)

    def batch_add_watermark(self):
        # TODO: use a cross-platform directory library
        if self.srcDirTextBox.text() and self.outDirTextBox.text():
            files = glob.glob(f'{self.srcDirTextBox.text()}/*.pdf')
            if files:
                num_files = len(files)
                s = "s" if num_files != 1 else ""
                if self.srcDirTextBox.text() == self.outDirTextBox.text():
                    if not self.show_msg_box(f"Are you sure you want to overwrite {num_files} file{s}?"):
                        return
                self.batchProgressBar.setValue(0)
                for i in range(len(files)):
                    src_file = files[i]
                    out_file = src_file.split("/")[-1].split("\]")[-1].split(".")[0]
                    if self.copyFilenameRadioBtn:
                        out_file += ".pdf"
                    elif self.addWatermarkedSuffixRadioBtn:
                        out_file += " watermarked.pdf"
                    elif self.addSuffixRadioBtn:
                        out_file += self.suffixTextBox.text() + ".pdf"
                    elif self.addPrefixRadioBtn:
                        out_file += self.prefixTextBox.text() + ".pdf"

                    marker.mark_pdf(src_file, f'{self.outDirTextBox.text()}/{out_file}', self.watermarkTxtBox.toPlainText())
                    self.batchProgressBar.setValue(int(i / len(files) * 100))
                self.batchProgressBar.setValue(100)
            else:
                self.show_msg_box(
                    text="Cannot find any PDFs.",
                    title="Error",
                    info=self.srcDirTextBox.text(),
                    icon=QMessageBox.Warning
                )
        else:
            src_invalid = not self.srcDirTextBox.text()
            out_invalid = not self.outDirTextBox.text()
            text = "Invalid "
            text += (("Source & " if out_invalid else "Source ") if src_invalid else "")
            text += "Output " if out_invalid else ""
            text += "Director" + ("ies" if src_invalid and out_invalid else "y") + "."
            self.show_msg_box(text=text, title="Error", icon=QMessageBox.Warning)

    def show_msg_box(self, text="", title="", info=None, icon=None, buttons=None):
        msg = QMessageBox(self)
        msg.setIcon(icon if icon is not None else QMessageBox.Information)
        if text is not None: msg.setText(text)
        if title is not None: msg.setWindowTitle(title)
        if info is not None: msg.setInformativeText(info)
        if buttons is not None: msg.setStandardButtons(buttons)
        msg.exec_()
            

    def update_preview(self):
        painter = QPainter()
        pagesize = self.previewPagesizeDropdown.currentText()
        orientation = self.previewOrientationDropdown.currentText().lower()
        if pagesize == "From File":
            if self.tabWidget.currentWidget() is self.singleTab:
                filename = self.singleSrcFileTxtBox.text()
                if filename and os.path.isfile(filename):
                    # TODO: Get these from the file
                    pagesize = pagesizes.letter
                    orientation = "landscape"
                else:
                    pagesize = pagesizes.letter
                    orientation = "landscape"
            elif self.tabWidget.currentWidget() is self.batchTab:
                pagesize = pagesizes.letter
                orientation = "landscape"
                # TODO: Get file from batch tab
        else:
            pagesize = self.pagesizes[pagesize]

        pageRatio = pagesize[0] / pagesize[1]
        if orientation == "landscape": pageRatio = 1 / pageRatio

        drawHeight = self.previewCanvas.height() - 10
        page = [
            drawHeight * pageRatio,
            drawHeight
        ]
        self.previewPixmap = QPixmap(self.previewCanvas.size())
        painter.begin(self.previewPixmap)
        painter.fillRect(0, 0, self.previewPixmap.width(), self.previewPixmap.height(), QColor(200, 200, 200))
        pageRect = [
            self.previewPixmap.width() / 2 - page[0] / 2,
            self.previewPixmap.height() / 2 - page[1] / 2,
            page[0],
            page[1]
        ]
        painter.fillRect(pageRect[0] - 1, pageRect[1] - 1, pageRect[2] + 2, pageRect[3] + 2, QColor(0, 0, 0))
        painter.fillRect(*pageRect, QColor(255, 255, 255))

        self.previewCanvas.setPixmap(self.previewPixmap)
