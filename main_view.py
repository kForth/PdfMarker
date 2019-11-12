from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QFileDialog

from marker import mark_pdf

import glob

class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        uic.loadUi('mainwindow.ui', self)

        # TODO: Load from config

        # TODO: Add color picker for text

        self.singleGoBtn.clicked.connect(self.mark_single_pdf)

        self.source_dir = ""
        self.output_dir = ""

        self.selectSrcDirBtn.clicked.connect(self.handle_select_src_dir_btn)
        self.selectOutDirBtn.clicked.connect(self.handle_select_out_dir_btn)
        self.goBtn.clicked.connect(self.batch_add_watermark)

        self.show()


    def mark_single_pdf(self):
        src_filename = QFileDialog.getOpenFileName(self, 'Open PDF', '', '*.pdf, *.PDF')[0]
        if not src_filename:
            return
        out_filename = QFileDialog.getSaveFileName(self, 'Save PDF', src_filename, '*.pdf, *.PDF')[0]
        if not out_filename:
            return
        mark_pdf(src_filename, out_filename, self.singleWatermarkTextBox.text())

    def handle_select_src_dir_btn(self):
        new_dir = QFileDialog.getExistingDirectory(self, 'Source Directory')
        if new_dir:
            self.source_dir = new_dir
            self.srcDirTextBox.setText(self.source_dir)

    def handle_select_out_dir_btn(self):
        new_dir = QFileDialog.getExistingDirectory(self, 'Output Directory')
        if new_dir:
            self.output_dir = new_dir
            self.outDirTextBox.setText(self.output_dir)

    def batch_add_watermark(self):
        # TODO: use a cross-platform directory library
        files = glob.glob(f'{self.source_dir}/*.pdf') + glob.glob(f'{self.source_dir}/*.PDF')
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

            mark_pdf(src_file, f'{self.output_dir}/{out_file}', self.batchWatermarkTextBox.text())
            self.batchProgressBar.setValue(int(i / len(files) * 100))
        self.batchProgressBar.setValue(100)

            

            
