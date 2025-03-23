from common import Asset
from common import FamilyCard
import os
from PIL import Image

class Card:
    def __init__(self, asset: Asset = None, familyCard: FamilyCard = None):
        self._asset = asset
        self._familyCard = familyCard
        assert((self._asset and self._familyCard == None)
               or (self._asset == None and self._familyCard))
        
    def isAsset(self) -> bool:
        return self._asset
        
    def isFamilyCard(self) -> bool:
        return self._familyCard
    
    def asset(self) -> Asset:
        return self._asset
    
    def familyCard(self) -> FamilyCard:
        return self._familyCard
    
    def value(self) -> int:
        if self.isAsset():
            return self._asset.value()
        else: #elif self.isFamilyCard():
            return self._familyCard.value()

    def points(self) -> int:
        if self.isAsset():
            return self._asset.points()
        else: #elif self.isFamilyCard():
            return self._familyCard.points()

    def __int__(self) -> int:
        if self.isAsset():
            return int(self._asset)
        else: #elif self.isFamilyCard():
            return int(self._familyCard)

    def __str__(self) -> str:
        if self.isAsset():
            return str(self._asset)
        else: #elif self.isFamilyCard():
            return str(self._familyCard)

    def name(self) -> str:
        if self.isAsset():
            return self._asset.name()
        else: #elif self.isFamilyCard():
            return self._familyCard.name()

    def imageName(self) -> str:
        if self.isAsset():
            return self._asset.imageName()
        else: #elif self.isFamilyCard():
            return self._familyCard.imageName()

    def image(self, cardSize):
        image = Image.open(os.path.dirname(__file__) + "/../../images/" + self.imageName() + ".png")

        image = image.resize(cardSize)
        
        return image

    def isOudler(self) -> bool:
        if self.isAsset():
            return self._asset.isOudler()
        else: #elif self.isFamilyCard():
            return False
