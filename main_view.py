from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QColorDialog, QFontDialog
from PyQt5.QtGui import QColor
from reportlab.pdfgen import canvas
from reportlab.lib import pagesizes, units

import marker

import glob
import io

class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        uic.loadUi('mainwindow.ui', self)

        self.single_tab_height = 130
        self.multi_tab_height = 222
        self.tab_height_diff = abs(self.multi_tab_height - self.single_tab_height)

        self.tabWidget.currentChanged.connect(self.updateTab)
        self.tabWidget.setCurrentIndex(1)  # TODO: From last session?
        self.updateTab(1)

        self.watermarkTxtBox.setText("Preliminary")  # TODO: Set text from config

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
        self.update_preview_page()

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
        self.singleOverwriteBtn.clicked.connect(self.handle_single_overwrite)
        self.singleSaveAsBtn.clicked.connect(self.handle_single_save_as)
        self.singleSelectSrcBtn.clicked.connect(self.handle_select_single_src_file)

        ## Batch PDF
        self.selectSrcDirBtn.clicked.connect(self.handle_batch_select_src_dir_btn)
        self.selectOutDirBtn.clicked.connect(self.handle_batch_select_out_dir_btn)
        self.goBtn.clicked.connect(self.batch_add_watermark)

        self.show()

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
        self.update_preview(page=True)      

    def set_watermark_font(self, font=None):
        if font is not None:
            marker.text_font = font
            self.update_preview(text=True)

    def set_watermark_color(self, *, color=None, opacity=None):
        if color is not None:
            self.colorLabel.setStyleSheet(self.watermark_color_label_style.format(color.name()))
            marker.text_color = [e/255.0 for e in color.getRgb()[:3]]
        if opacity is not None:
            marker.text_opacity = opacity
        self.update_preview(text=True)

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
            self.setMinimumHeight(550 - self.tab_height_diff)
            preview_height -= self.tab_height_diff
        elif tab == 1:
            self.tabWidget.setFixedHeight(self.multi_tab_height)
            self.setMinimumHeight(550)
            preview_height += self.tab_height_diff
        self.resize(self.width(), preview_height)

    def handle_select_single_src_file(self):
        filename = QFileDialog.getOpenFileName(self, 'Open PDF', '', '*.pdf, *.PDF')[0]
        if filename:
            self.single_src_filename = filename
            self.singleSrcFileTxtBox.setText(self.single_src_filename)

    def handle_single_overwrite(self):
        self.setEnabled(False)
        text = self.singleWatermarkTextBox.text()
        if text: 
            if self.single_src_filename:
                marker.mark_pdf(self.single_src_filename, self.single_src_filename, text)
                self.show_msg_box("Done", "Done", "Saved as " + self.single_src_filename.split("/")[-1], buttons=QMessageBox.Ok)
        self.setEnabled(True)

    def handle_single_save_as(self):
        self.setEnabled(False)
        text = self.singleWatermarkTextBox.text()
        if text: 
            if self.single_src_filename: 
                out_filename = QFileDialog.getSaveFileName(self, 'Save PDF', self.single_src_filename, '*.pdf, *.PDF')[0]
                if out_filename:
                    marker.mark_pdf(self.single_src_filename, out_filename, text)
                    self.show_msg_box("Done", "Done", "Saved as " + out_filename.split("/")[-1], buttons=QMessageBox.Ok)
        self.setEnabled(True)

    def handle_batch_select_src_dir_btn(self):
        new_dir = QFileDialog.getExistingDirectory(self, 'Source Directory')
        if new_dir:
            self.batch_source_dir = new_dir
            self.srcDirTextBox.setText(self.batch_source_dir)

    def handle_batch_select_out_dir_btn(self):
        new_dir = QFileDialog.getExistingDirectory(self, 'Output Directory')
        if new_dir:
            self.batch_output_dir = new_dir
            self.outDirTextBox.setText(self.batch_output_dir)

    def batch_add_watermark(self):
        # TODO: use a cross-platform directory library
        if self.batch_source_dir and self.batch_output_dir:
            files = glob.glob(f'{self.batch_source_dir}/*.pdf') + glob.glob(f'{self.batch_source_dir}/*.PDF')
            num_files = len(files)
            s = "s" if num_files != 1 else ""
            if self.batch_source_dir == self.batch_output_dir:
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

                marker.mark_pdf(src_file, f'{self.batch_output_dir}/{out_file}', self.batchWatermarkTextBox.text())
                self.batchProgressBar.setValue(int(i / len(files) * 100))
            self.batchProgressBar.setValue(100)

    def show_msg_box(self, text="", title="", info=None, icon=None, buttons=None):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setText("Done")
        msg.setInformativeText()
        msg.setWindowTitle("Done")
        msg.setStandardButtons()
        msg.exec_()
            

    def update_preview(self, page=False, text=False):
        print("TODO: Update " + ("page" if page else "") + (" & " if page and text else "") + ("text" if text else ""))
