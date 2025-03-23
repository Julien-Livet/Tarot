from enum import Enum
from PyQt5.QtCore import QCoreApplication

class Head(Enum):
    Jack = 0
    Knight = 1
    Queen = 2
    King = 3

    def __int__(self) -> int:
        return self.value
    
    def name(self) -> str:
        if (self.value == 0):
            return QCoreApplication.translate("name", "Jack")
        elif (self.value == 1):
            return QCoreApplication.translate("name", "Knight")
        elif (self.value == 2):
            return QCoreApplication.translate("name", "Queen")
        elif (self.value == 3):
            return QCoreApplication.translate("name", "King")
        else:
            return ""

    def __str__(self) -> str:
        return self.name()
