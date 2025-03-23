from enum import Enum
from PyQt5.QtCore import QCoreApplication

class Family(Enum):
    Heart = 0
    Diamond = 1
    Club = 2
    Spade = 3

    def __int__(self) -> int:
        return self.value
    
    def name(self) -> str:
        if (self.value == 0):
            return QCoreApplication.translate("name", "Heart")
        elif (self.value == 1):
            return QCoreApplication.translate("name", "Diamond")
        elif (self.value == 2):
            return QCoreApplication.translate("name", "Club")
        elif (self.value == 3):
            return QCoreApplication.translate("name", "Spade")
        else:
            return ""

    def __str__(self) -> str:
        return self.name()
