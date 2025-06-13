import sys

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QStyleFactory

from pdf_marker.main_view import MainWindow

app = QtWidgets.QApplication(sys.argv)
# app.setWindowIcon(QtGui.QIcon("icon.ico"))
app.setStyle(QStyleFactory.create("fusion"))

window = MainWindow()
sys.exit(app.exec_())
