from PyQt5.QtCore import QCoreApplication

class Asset:
    def __init__(self, value: int):
        self._value = value
        assert(0 <= self._value and self._value <= 21)
    
    def isFool(self) -> bool:
        return self._value == 0
    
    def isOudler(self) -> bool:
        return self._value == 0 or self._value == 1 or self._value == 21
        
    def value(self) -> int:
        return self._value

    def points(self) -> int:
        if (self.isOudler()):
            return 4.5
        else:
            return 0.5
    
    def __int__(self) -> int:
        return self.value()

    def name(self) -> str:
        if (self.value() == 0):
            return QCoreApplication.translate("name", "Fool")
            
        return QCoreApplication.translate("name", "Asset {0}").format(self.value())

    def imageName(self) -> str:
        return "asset-"+ str(self.value())

    def __str__(self) -> str:
        return self.name()
