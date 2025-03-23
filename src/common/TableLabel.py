from PyQt5.QtWidgets import QLabel

class TableLabel(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self._mousePressPos = None
        self._pressed = False
        
    def mousePressEvent(self, event):
        if (not self._pressed):
            self._mousePressPos = event.pos()
        else:
            self._mousePressPos = None

    def mouseReleaseEvent(self, event):
        self._mousePressPos = None
        self._pressed = False
