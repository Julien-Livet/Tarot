from enum import Enum
from PyQt5.QtCore import QCoreApplication

class Contract(Enum):
    Little = 0
    Guard = 1
    GuardWithout = 2
    GuardAgainst = 3
    
    def __int__(self) -> int:
        return self.value
    
    def name(self) -> str:
        if (self.value == 0):
            return QCoreApplication.translate("name", "Little")
        elif (self.value == 1):
            return QCoreApplication.translate("name", "Guard")
        elif (self.value == 2):
            return QCoreApplication.translate("name", "Guard without")
        elif (self.value == 3):
            return QCoreApplication.translate("name", "Guard against")
        else:
            return ""

    def __str__(self) -> str:
        return self.name()
