from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox

from marker import mark_pdf

import glob

class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        uic.loadUi('mainwindow.ui', self)

        # TODO: Load from config

        # TODO: Add color picker for text

        self.tabWidget.currentChanged.connect(self.updateTab)
        self.tabWidget.setCurrentIndex(1)  # TODO: From last session?
        self.updateTab(1)

        self.singleOverwriteBtn.clicked.connect(self.handle_single_overwrite)
        self.singleSaveAsBtn.clicked.connect(self.handle_single_save_as)
        self.singleSelectSrcBtn.clicked.connect(self.handle_select_single_src_file)

        self.single_src_filename = ""
        self.batch_source_dir = ""
        self.batch_output_dir = ""

        self.selectSrcDirBtn.clicked.connect(self.handle_batch_select_src_dir_btn)
        self.selectOutDirBtn.clicked.connect(self.handle_batch_select_out_dir_btn)
        self.goBtn.clicked.connect(self.batch_add_watermark)

        self.show()

    def updateTab(self, tab):
        if tab == 0:
            # self.minimumHeight = self.maximumHeight = 133
            self.setFixedHeight(185)
        elif tab == 1:
            # self.minimumHeight = self.maximumHeight = 355
            self.setFixedHeight(290)

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
                mark_pdf(self.single_src_filename, self.single_src_filename, text)
                self.show_msg_box("Done", "Done", "Saved as " + self.single_src_filename.split("/")[-1], buttons=QMessageBox.Ok)
        self.setEnabled(True)

    def handle_single_save_as(self):
        self.setEnabled(False)
        text = self.singleWatermarkTextBox.text()
        if text: 
            if self.single_src_filename: 
                out_filename = QFileDialog.getSaveFileName(self, 'Save PDF', self.single_src_filename, '*.pdf, *.PDF')[0]
                if out_filename:
                    mark_pdf(self.single_src_filename, out_filename, text)
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
        files = glob.glob(f'{self.batch_source_dir}/*.pdf') + glob.glob(f'{self.batch_source_dir}/*.PDF')
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

            mark_pdf(src_file, f'{self.batch_output_dir}/{out_file}', self.batchWatermarkTextBox.text())
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
            

            
