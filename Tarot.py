from enum import Enum
import io
import math
from PIL import Image, ImageTk
from PyQt5 import QtTest
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QComboBox, QDialog, QHBoxLayout, QMessageBox, QVBoxLayout, QLabel, QPushButton, QWidget
import random
import sys
import time
import threading

cardSize = (56, 109)

class GUI:
    def __init__(self):
        self._playerNumber = 5
        self._window = None
        self._dialog = None
        self._ok = False

    def threePlayers(self):
        self._playerNumber = 3
        self._dialog.accept()
    
    def fourPlayers(self):
        self._playerNumber = 4
        self._dialog.accept()
    
    def fivePlayers(self):
        self._playerNumber = 5
        self._dialog.accept()
    
    def displayTable(self, centerCards: list, displayCenterCards: bool = False):
        img = self._game.tableImage(self._showPlayers, centerCards, displayCenterCards)
        scale = 0.85
        img = img.resize((int(img.width * scale),
                          int(img.height * scale)))

        byteArray = io.BytesIO()
        img.save(byteArray, format = 'PNG')
        pixmap = QPixmap()
        pixmap.loadFromData(byteArray.getvalue())
        self._tableLabel.setPixmap(pixmap)

    def play(self) -> bool:
        self._dialog = QDialog()
        self._dialog.setWindowTitle("Choose a game")
        
        layout = QVBoxLayout()

        threeButton = QPushButton("Three players", self._dialog)
        threeButton.clicked.connect(self.threePlayers)
        fourButton = QPushButton("Four players", self._dialog)
        fourButton.clicked.connect(self.fourPlayers)
        fiveButton = QPushButton("Five players", self._dialog)
        fiveButton.clicked.connect(self.fivePlayers)
        
        layout.addWidget(threeButton)
        layout.addWidget(fourButton)
        layout.addWidget(fiveButton)
        
        self._dialog.setLayout(layout)
        
        self._dialog.exec()
            
        if (self._dialog.result() == QDialog.Rejected):
            return True

        self._game = Game(self._playerNumber)
        self._game.giveHands()
        self._game._players[0]._isHuman = True
        self._showPlayers = [False for i in range(0, self._playerNumber)]
        self._showPlayers[0] = True #self._showPlayers[random.randrange(self._playerNumber)] = True

        self._window = QDialog()
        self._window.setWindowTitle("Tarot")

        self._tableLabel = QLabel(self._window)
        self.displayTable(self._game._dog, False)
        self._pointsLabel = QLabel("Attack points: 0 - Defence points: 0", self._window)
        self._pointsLabel.setAlignment(Qt.AlignCenter)
        
        self._contractLabel = QLabel("Choose a contract", self._window)
        self._contractLabel.setVisible(False)
        self._contractComboBox = QComboBox(self._window)
        self._contractComboBox.setVisible(False)

        choices = []
        
        for i in range(0, 4):
            choices.append(str(Family(i)))
        
        self._kingLabel = QLabel("Call a king", self._window)
        self._kingLabel.setVisible(False)
        self._kingComboBox = QComboBox(self._window)
        self._kingComboBox.addItems(choices)
        self._kingComboBox.setVisible(False)
        
        self._dogLabel = QLabel("Do a dog", self._window)
        self._dogLabel.setVisible(False)
        self._dogComboBoxes = []
        for i in range(0, 6):
            self._dogComboBoxes.append(QComboBox(self._window))
            self._dogComboBoxes[-1].setVisible(False)
        
        self._cardLabel = QLabel("Play a card", self._window)
        self._cardLabel.setVisible(False)
        self._cardComboBox = QComboBox(self._window)
        self._cardComboBox.setVisible(False)
        
        okButton = QPushButton("OK", self._window)
        okButton.clicked.connect(self.ok)

        verticalLayout = QVBoxLayout()
        verticalLayout.addWidget(self._contractLabel)
        verticalLayout.addWidget(self._contractComboBox)
        verticalLayout.addWidget(self._kingLabel)
        verticalLayout.addWidget(self._kingComboBox)
        verticalLayout.addWidget(self._dogLabel)
        for i in range(0, 6):
            verticalLayout.addWidget(self._dogComboBoxes[i])
        verticalLayout.addWidget(self._cardLabel)
        verticalLayout.addWidget(self._cardComboBox)
        verticalLayout.addWidget(okButton)
        
        horizontalLayout = QHBoxLayout()
        layout = QVBoxLayout()
        
        layout.addWidget(self._tableLabel)
        layout.addWidget(self._pointsLabel)
        horizontalLayout.addLayout(layout)        
        horizontalLayout.addLayout(verticalLayout)
        
        self._window.setLayout(horizontalLayout)
        
        self._window.show()

        self._thread = threading.Thread(target = self._game.play, args = (self, ), daemon = True)
        self._thread.start()

        self._timer = QTimer(self._window)
        self._timer.setInterval(10)
        self._timer.timeout.connect(self.monitor)
        self._timer.start()
        
        return False
        
    def ok(self):
        self._ok = True
        
    def monitor(self):
        take = ""
        
        if (self._game._calledKing):
            take = " - Called king: " + str(self._game._calledKing)
    
        self._pointsLabel.setText("Attack points: "
                                  + str(self._game.attackPoints())
                                  + " - Defence points: "
                                  + str(self._game.defencePoints())
                                  + take)
    
        if (not self._thread.is_alive()):
            if (self._game.attackPoints() == 0
                and self._game.defencePoints() == 0):
                QMessageBox.information(self._window, "Game over", "Nobody takes!")
                
                self._window.close()
                
                self.play()
            else:
                if (self._game.attackWins()):
                     QMessageBox.information(self._window,
                                             "Game over",
                                             "Attack wins ("
                                             + str(self._game.attackPoints())
                                             + " points for "
                                             + str(self._game.attackTargetPoints())
                                             + " points)!")
                else:
                     QMessageBox.information(self._window,
                                             "Game over",
                                             "Attack loses ("
                                             + str(self._game.attackPoints())
                                             + " points for "
                                             + str(self._game.attackTargetPoints())
                                             + " points)!")
                
                self._window.close()

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
        return "asset-"+ str(self.value())

    def __str__(self) -> str:
        return self.name()

class Contract(Enum):
    Little = 0
    Guard = 1
    GuardWithout = 2
    GuardAgainst = 3
    
    def __int__(self) -> int:
        return self.value
    
    def __str__(self) -> str:
        if (self.value == 0):
            return "Little"
        elif (self.value == 1):
            return "Guard"
        elif (self.value == 2):
            return "Guard without"
        elif (self.value == 3):
            return "Guard against"
        else:
            return ""

class Family(Enum):
    Heart = 0   #Coeur
    Diamond = 1 #Carreau
    Club = 2    #Trèfle
    Spade = 3   #Pique

    def __int__(self) -> int:
        return self.value
    
    def __str__(self) -> str:
        if (self.value == 0):
            return "Heart"
        elif (self.value == 1):
            return "Diamond"
        elif (self.value == 2):
            return "Club"
        elif (self.value == 3):
            return "Spade"
        else:
            return ""

class Head(Enum):
    Jack = 0
    Knight = 1
    Queen = 2
    King = 3

    def __int__(self) -> int:
        return self.value
    
class FamilyCard:
    def __init__(self, family: Family, head: Head = None, value: int = None):
        self._family = family
        self._value = value
        self._head = head
        assert((self._value and self._head == None)
               or (self._value == None and self._head))
        if (self._value):
            assert(1 <= self._value and self._value <= 10)
    
    def isFamily(self, family: Family) -> bool:
        return self._family == family

    def family(self) -> Family:
        return self._family
        
    def name(self) -> str:
        s = ""
        
        if self._family == Family.Heart:
            s = "heart"
        elif self._family == Family.Diamond:
            s = "diamond"
        elif self._family == Family.Club:
            s = "club"
        elif self._family == Family.Spade:
            s = "spade"
            
        return s + "-" + str(self.value())

    def value(self) -> int:
        if (self._head):
            return 11 + int(self._head)
        else:
            return self._value
            
    def points(self) -> int:
        if (self._value):
            return 0.5
        else:
            return self._head._value + 1 + 0.5

    def __int__(self) -> int:
        return self.value()

    def __str__(self) -> str:
        return self.name()

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

    def image(self):
        image = Image.open("images/" + self.name() + ".png")
        
        image = image.resize(cardSize)
        
        return image

    def isOudler(self) -> bool:
        if self.isAsset():
            return self._asset.isOudler()
        else: #elif self.isFamilyCard():
            return False

def countOudlersForCards(cards: list) -> int:
    count = 0

    for card in cards:
        if (card.isOudler()):
            count += 1

    return count

def imageForCards(cards: list, shown: bool = True, ratio: float = 1 / 3):
    assert(0.0 < ratio and ratio < 1.0)

    if (len(cards) == 0):
        return None
    
    firstImage = None
    
    if (shown):
        firstImage = cards[0].image()
    else:
        firstImage = Image.open("images/back.png")
        
        firstImage = firstImage.resize(cardSize)
    
    image = Image.new('RGBA', (firstImage.width + int((len(cards) - 1) * firstImage.width * ratio), firstImage.height))
    
    for i in range(0, len(cards)):
        im = None
        
        if (shown):
            im = cards[i].image()
        else:
            im = firstImage
            
        image.paste(im, (int(i * firstImage.width * ratio), 0))
    
    return image

def pointsForCards(cards: list) -> int:
    points = 0
    
    for card in folds:
        points += card.points()
        
    return points

def sortCards(cards: list) -> list:
    assets = []
    families = {Family.Heart: [],
                Family.Club: [],
                Family.Diamond: [],
                Family.Spade: []}
    for card in cards:
        if card.isAsset():
            assets.append(card)
        else: #elif card.isFamilyCard():
            families[card.familyCard().family()].append(card)
    assets = sorted(assets, key=lambda x: x.value(), reverse=True)
    for k, v in families.items():
        families[k] = sorted(families[k], key=lambda x: x.value(), reverse=True)
    cards = assets
    if (len(families[Family.Club]) == 0):
        families[Family.Club], families[Family.Spade] = families[Family.Spade], families[Family.Club]
    if (len(families[Family.Diamond]) == 0):
        families[Family.Diamond], families[Family.Heart] = families[Family.Heart], families[Family.Diamond]
    families = [x[1] for x in families.items()]
    for f in families:
        cards += f
        
    return cards

class Player:
    def __init__(self):
        self._folds = []
        self._cards = []
        self._attackTeam = False
        self._teamKnown = False
        self._isHuman = False
        
    def isHuman(self):
        return self._isHuman
    
    def points(self) -> int:
        points = 0
        
        for fold in self._folds:
            points += pointsForCards(fold)

        return points
                
    def folds(self) -> list:
        return self._folds
        
    def cards(self) -> list:
        return self._cards
        
    def attackTeam(self) -> bool:
        return self._attackTeam
        
    def defenceTeam(self) -> bool:
        return not self._attackTeam
        
    def teamKnown(self) -> bool:
        return self._teamKnown
        
    def handImage(self):
        return imageForCards(self._cards)
        
    def chooseContract(self, gui: GUI, contract: Contract) -> Contract:
        possibleContracts = []
        
        if (contract):
            possibleContracts = [i for i in range(int(contract) + 1, 4)]
        else:
            possibleContracts = [i for i in range(-1, 4)]
            
        if (len(possibleContracts) == 0):
            return None
        
        strContracts = {}
        strContracts[-1] = "Pass"
        
        for i in range(0, 4):
            strContracts[i] = str(Contract(i))
        
        choices = [strContracts[i] for i in possibleContracts]

        if (self._isHuman):
            gui._contractLabel.setVisible(True)
            gui._contractComboBox.clear()
            gui._contractComboBox.addItems(choices)
            gui._contractComboBox.setVisible(True)
            gui._ok = False
            
            while (not gui._ok):
                QtTest.QTest.qWait(10)
            
            contract = {v: k for k, v in strContracts.items()}.get(choices[gui._contractComboBox.currentIndex()])
            
            gui._contractLabel.setVisible(False)
            gui._contractComboBox.setVisible(False)

            if (contract == -1):
                return None
            else:
                return Contract(contract)
        else:
            #TODO: ...
            
            return None
    
    def callKing(self, gui: GUI) -> Family:
        strFamilies = {}
        choices = []
        
        for i in range(0, 4):
            strFamilies[i] = str(Family(i))
            choices.append(str(Family(i)))
        
        calledKing = None
        
        if (self._isHuman):
            gui._kingLabel.setVisible(True)
            gui._kingComboBox.setVisible(True)
            gui._ok = False
            
            while (not gui._ok):
                QtTest.QTest.qWait(10)
            
            calledKing = {v: k for k, v in strFamilies.items()}.get(choices[gui._kingComboBox.currentIndex()])
            
            gui._kingLabel.setVisible(False)
            gui._kingComboBox.setVisible(False)
        else:
            #TODO: ...
            
            pass

        return Family(calledKing)
    
    def doDog(self, dog: list, gui: GUI) -> list:
        newDog = []
        
        self._cards += dog
        self._cards = sortCards(self._cards)
        
        gui.displayTable([])

        if (self._isHuman):
            comboBoxes = []
            
            strCards = {}
            choices = []
            
            for i in range(0, len(self._cards)):
                if (not (self._cards[i].isAsset()
                         or (self._cards[i].isFamilyCard()
                             and self._cards[i].familyCard().value() == 14))):
                    strCards[i] = str(self._cards[i])
                    choices.append(str(self._cards[i]))
            
            gui._dogLabel.setVisible(True)
            
            for i in range(0, len(dog)):
                gui._dogComboBoxes[i].clear()
                gui._dogComboBoxes[i].addItems(choices)
                gui._dogComboBoxes[i].setVisible(True)

            loop = True
            
            while (loop):
                gui._ok = False
                
                while (not gui._ok):
                    QtTest.QTest.qWait(10)
  
                selectedCards = []
                
                for i in range(0, len(dog)):
                    selectedCards.append(choices[gui._dogComboBoxes[i].currentIndex()])
                
                loop = len(set(selectedCards)) != len(dog)
            
            gui._dogLabel.setVisible(False)
            
            for i in range(0, len(dog)):
                gui._dogComboBoxes[i].setVisible(False)
                          
            d = {v: k for k, v in strCards.items()}
            
            for i in range(0, len(dog)):
                selectedCards[i] = d.get(selectedCards[i])
            
            selectedCards = sorted(selectedCards)
            
            for i in reversed(range(0, len(dog))):
                j = selectedCards[i]
                newDog.append(self._cards[j])
                del self._cards[j]
        else:
            #TODO: ...

            pass
        
        assert(len(newDog) == len(dog))
        
        return sortCards(newDog)

    def playCard(self, cards: dict, firstRound: bool, calledKing: Family) -> Card:
        QtTest.QTest.qWait(1000)

        card = None

        strCards = {}
        choices = []

        cardAssets = []
        
        cardList = [x[1] for x in cards.items()]
        
        gui.displayTable(cardList, True)
        
        for card in cardList:
            if (card.isAsset()):
                cardAssets.append(card)
                
        cardAssets = sorted(cardAssets, key=lambda x: x.value())
        
        handAssets = []
        handFamilies = {Family.Heart: [],
                        Family.Diamond: [],
                        Family.Club: [],
                        Family.Spade: []}
        
        for i in range(0, len(self._cards)):
            if (self._cards[i].isAsset()):
                handAssets.append(self._cards[i])
            else:
                handFamilies[self._cards[i].familyCard().family()].append(self._cards[i])
 
        handAssets = sorted(handAssets, key=lambda x: x.value())
        
        for i in range(0, len(self._cards)):
            add = True
            
            if (firstRound):
                if (len(cardList) == 0):
                    if (self._cards[i].isFamilyCard()
                        and self._cards[i].familyCard().family() == calledKing
                        and self._cards[i].familyCard().value() != 14):
                        add = False
            else:
                if (len(cardList)):
                    firstCard = cardList[0]
                    
                    if (firstCard.isAsset() and firstCard.asset().isFool()):
                        if (len(cardList) > 0):
                            firstCard = cardList[1]
                        else:
                            firstCard = None

                    if (firstCard):
                        if (firstCard.isAsset()):
                            if (len(handAssets)):
                                if (self._cards[i].isAsset()):
                                    if (handAssets[-1].value() > cardAssets[-1].value()
                                        and self._cards[i].asset().value() < cardAssets[-1].value()):
                                        add = False
                                else:
                                    add = False
                        else:
                            if (self._cards[i].isAsset()):
                                if (len(handFamilies[firstCard.familyCard().family()])):
                                    if (not self._cards[i].asset().isFool()):
                                        add = False
                                else:
                                    if (len(cardAssets)):
                                        if (handAssets[-1].value() > cardAssets[-1].value()
                                            and self._cards[i].asset().value() < cardAssets[-1].value()):
                                            add = False
                            else:
                                if (self._cards[i].familyCard().family() != firstCard.familyCard().family()
                                    and len(handAssets)):
                                    add = False

            if (add):
                strCards[i] = str(self._cards[i])
                choices.append(str(self._cards[i]))

        if (self._isHuman):
            gui._cardLabel.setVisible(True)
            gui._cardComboBox.clear()
            gui._cardComboBox.addItems(choices)
            gui._cardComboBox.setVisible(True)
            gui._ok = False
            
            while (not gui._ok):
                QtTest.QTest.qWait(10)
            
            gui._cardLabel.setVisible(False)
            gui._cardComboBox.setVisible(False)
            
            selectedCard = {v: k for k, v in strCards.items()}.get(choices[gui._cardComboBox.currentIndex()])

            card = self._cards[selectedCard]
            del self._cards[selectedCard]
        else:
            selectedCard = random.randrange(len(choices))
            selectedCard = {v: k for k, v in strCards.items()}.get(choices[selectedCard])
            
            card = self._cards[selectedCard]
            del self._cards[selectedCard]
        
        return card
    
class Game:
    def __init__(self, playerNumber: int = 5):
        self._cards = []
        self._hands = []
        self._dog = []
        self._players = []
        self._contract = None
        self._calledKing = None
        self._playerNumber = playerNumber
        self._firstPlayer = None
        self._taker = None
        self._foolPlayed = None
        self._foolCardGiven = False
        assert(3 <= self._playerNumber and self._playerNumber <= 5)
    
    def play(self, gui):
        self._firstPlayer = random.randrange(self._playerNumber)
        
        for i in range(0, self._playerNumber):
            p = (self._firstPlayer + i) % self._playerNumber
            contract = self._players[p].chooseContract(gui, self._contract)
            if (contract):
                self._taker = p
                self._contract = contract
        
        if (not self._contract):
            return

        self._players[self._taker]._attackTeam = True
        self._players[self._taker].knownTeam = True

        if (self._playerNumber == 5):
            self._calledKing = self._players[self._taker].callKing(gui)
        else:
            for i in range(0, len(self._players)):
                if (i != self._taker):
                    self._players[i]._attackTeam = False
                    self._players[i].teamKnown = True

        if (self._contract == Contract.Little
            or self._contract == Contract.Guard):
            gui.displayTable(self._dog, True)
            QtTest.QTest.qWait(1000)

            kingInDog = False

            for card in self._dog:
                if (card.isFamilyCard()
                    and card.familyCard().family() == self._calledKing
                    and card.familyCard().value() == 14):
                    kingInDog = True
                    break

            if (not kingInDog):
                found = False

                for i in range(0, len(self._players)):
                    for card in self._players[i].cards():
                        if (card.isFamilyCard()
                            and card.familyCard().family() == self._calledKing
                            and card.familyCard().value() == 14):
                            self._players[i]._attackTeam = True
                            found = True
                            break
                    
                    if (found):
                        break
            else:
                for i in range(0, len(self._players)):
                    if (i != self._taker):
                        self._players[i]._attackTeam = False
                        self._players[i].teamKnown = True

            self._dog = self._players[self._taker].doDog(self._dog, gui)

        n = int((78 - len(self._dog)) / self._playerNumber)

        for i in range(0, n):
            cards = {}

            for i in range(0, self._playerNumber):
                p = (self._firstPlayer + i) % self._playerNumber
                cards[p] = self._players[p].playCard(cards, i == 0, self._calledKing)

            self._firstPlayer = self.playSet(cards, i == n - 1)

        gui.displayTable(self._dog, True)

        if (self._contract == Contract.GuardWithout):
            for p in self._players:
                if (p.defenceTeam()):
                    p._cards += self._dog
                    break
        else:
            self._players[self._taker]._cards += self._dog

        self._dog = []

    def attackPoints(self):
        points = 0

        for p in self._players:
            if p.teamKnown() and p.attackTeam():
                points += p.points()
        
        return points

    def attackCards(self):
        cards = []

        for p in self._players:
            if p.teamKnown() and p.attackTeam():
                cards += p._cards
        
        return cards

    def attackFolds(self):
        folds = []

        for p in self._players:
            if p.teamKnown() and p.attackTeam():
                folds += p.folds()
        
        return folds

    def defencePoints(self):
        points = 0

        for p in self._players:
            if p.teamKnown() and p.defenceTeam():
                points += p.points()
        
        return points

    def defenceCards(self):
        cards = []

        for p in self._players:
            if p.teamKnown() and p.defenceTeam():
                cards += p._cards
        
        return cards

    def defenceFolds(self):
        folds = []

        for p in self._players:
            if p.teamKnown() and p.defenceTeam():
                folds += p.folds()
        
        return folds

    def giveFoolCard(self):
        if (not self._foolPlayed):
            return
        elif (self._foolCardGiven):
            return
            
        defencePlayer = -1
        attackPlayer = -1
        
        for i in range(0, self.playerNumber):
            if (self._players[i].defenceTeam()):
                defencePlayer = i
            else:
                attackPlayer = i
            if (defencePlayer != -1 and attackPlayer != -1):
                break
                
        folds = []
                
        if (self._foolPlayed[0]):
            folds = self.attackFolds()
        else:
            folds = self.defenceFolds()
        
        folds = sorted(folds, key=lambda x: x.points())
            
        givenCard = None
            
        if (len(folds) > 1):
            givenCard = folds[0]
            self._foolCardGiven = True
            
        if (givenCard):
            for player in self._players:
                if (givenCard in self._players._cards):
                    del self._players._cards[self._players._cards.index(givenCard)]
                    break

            if (self._foolPlayed[0]):
                self._players[defencePlayer]._folds.append(givenCard)
            else:
                self._players[attackPlayer]._folds.append(givenCard)

    def giveHands(self):
        self._foolPlayed = None
        self._foolCardGiven = False
        self._cards = []
        for i in range(0, 4):
            for j in range(1, 11):
                self._cards.append(Card(familyCard = FamilyCard(family = Family(i), value = j)))
            for j in range(0, 4):
                self._cards.append(Card(familyCard = FamilyCard(family = Family(i), head = Head(j))))
        for i in range(0, 22):
            self._cards.append(Card(asset = Asset(i)))
        random.shuffle(self._cards)
        assert(len(self._cards) == 78)
        
        self._players = [Player() for x in range(0, self._playerNumber)]
        
        n = int(78 / 3 / self._playerNumber)
        
        for i in range(0, n):
            for j in range(0, len(self._players)):
                self._players[j]._cards += self._cards[0:3]
                self._cards = self._cards[3:]
        
        #for p in self._players:
        for i in range(0, self._playerNumber):
            player = self._players[i]
            player._cards = sortCards(player._cards)
        
        self._dog = sortCards(self._cards)
        self._cards = []
    
    def playSet(self, cards: dict, lastSet: bool):
        assets = {}
        families = {Family.Heart: {},
                    Family.Diamond: {},
                    Family.Club: {},
                    Family.Spade: {}}
        for k, v in cards.items():
            if v.isAsset():
                assets[k] = v
            else: #elif v.isFamilyCard():
                families[v.familyCard().family()][k] = v.familyCard()

        assets = dict(sorted(assets.items(), key=lambda x: x[1].value()))
        for i in range(0, 4):
            families[Family(i)] = dict(sorted(families[Family(i)].items(), key=lambda x: x[1].value()))

        foolIndex = -1
        
        for i in range(0, len(assets.items())):
            if (list(assets.items())[i][1].asset().isFool()):
                foolIndex = i
                break

        if (len(assets)):
            a = [x[1] for x in assets.items()]
            if (foolIndex != -1):
                p = list(assets.items())[foolIndex][0]
                if (lastSet):
                    attackTeam = self._players[p].attackTeam()
                    
                    if (attackTeam):
                        for i in range(0, self.playerNumber):
                            if (self._players[i].defenceTeam()):
                                self._players[i]._folds += assets.items()[foolIndex][1]
                                del assets[i]
                                break
                    else:
                        for i in range(0, self.playerNumber):
                            if (self._players[i].attackTeam()):
                                self._players[i]._folds += assets.items()[foolIndex][1]
                                del assets[i]
                                break
                else:
                    self._players[p]._folds += assets.items()[foolIndex][1]
                    del assets[p]
            if (len(assets)):
                p = list(assets.items())[-1][0]
                self._players[p]._folds += [x[1] for x in cards.items()]
                return p
        
        f = list(cards.items())[0][1].familyCard().family()
        p = list(families[f].items())[-1][0]
        self._players[p]._folds += [x[1] for x in cards.items()]
        
        self.giveFoolCard()
        
        return p

    def attackTargetPoints(self):
        cards = self.attackCards()
        
        points = 56
        oudlerCount = countOudlersForCards(cards)

        if (oudlerCount == 3):
            points = 36
        elif (points == 2):
            points = 41
        elif (oudlerCount == 1):
            points = 51
            
        return points

    def defenceTargetPoints(self):
        cards = self.defenceCards()
        
        points = 56
        oudlerCount = countOudlersForCards(cards)

        if (oudlerCount == 3):
            points = 36
        elif (points == 2):
            points = 41
        elif (oudlerCount == 1):
            points = 51
            
        return points

    def attackWins(self):
        return self.attackPoints() >= self.attackTargetPoints()

    def defenceWins(self):
        return not self.attackWins()

    def tableImage(self, showPlayers: list, centerCards: list, showCenterCards: bool):
        assert(len(showPlayers) == self._playerNumber)
        
        tableImage = Image.new('RGBA', (1024, 768), color=(139, 69, 19))
        
        centerCardsImage = imageForCards(centerCards, shown = showCenterCards)
        
        if (centerCardsImage):
            tableImage.paste(centerCardsImage, (int((tableImage.width - centerCardsImage.width) / 2),
                                                int((tableImage.height - centerCardsImage.height) / 2)))
        
        radius = 300
        
        if (self._playerNumber == 4):
            radius = 275
        elif (self._playerNumber == 3):
            radius = 225
        
        positions = [(int(tableImage.width / 2),
                      int(tableImage.height / 2 + radius))]
        angles = [0]

        for i in range(1, self._playerNumber):
            angles.append(angles[-1] - 360 / self._playerNumber)
            x = tableImage.width / 2 + radius * math.sin(math.radians(angles[-1]))
            y = tableImage.height / 2 + radius * math.cos(math.radians(angles[-1]))
            positions.append((x, y))

        for i in range(0, self._playerNumber):
            playerCardsImage = imageForCards(self._players[i]._cards, shown = showPlayers[i])
            
            if (playerCardsImage):
                x = positions[i][0]
                y = positions[i][1]
                img = playerCardsImage.rotate(angles[i], expand = True)
                x -= img.width / 2
                y -= img.height / 2
                image = Image.new('RGBA', (tableImage.width, tableImage.height))
                image.paste(img, (int(x), int(y)))
                tableImage = Image.alpha_composite(tableImage, image)
        
        return tableImage

app = QApplication(sys.argv)

gui = GUI()

if (not gui.play()):
    sys.exit(app.exec_())
