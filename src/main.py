from client import GUI
import os
from PyQt5.QtCore import QLocale, QTranslator
from PyQt5.QtWidgets import QApplication
import sys

if (__name__ == "__main__"):
    app = QApplication(sys.argv)
    translator = QTranslator()
    translator.load(os.path.dirname(__file__) + "/../Tarot_" + QLocale.system().name() + ".qm")
    app.installTranslator(translator)

    gui = GUI.GUI()

    if (not gui.play()):
        sys.exit(app.exec_())
