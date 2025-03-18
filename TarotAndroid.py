from enum import Enum
import io
import kivy.app
import kivy.clock
import kivy.core
import kivy.core.image
import kivy.uix
import kivy.uix.boxlayout
import kivy.uix.button
import kivy.uix.gridlayout
import kivy.uix.image
import kivy.uix.label
import kivy.uix.spinner
import math
from PIL import Image, ImageDraw, ImageFont
import random
import sys
import time
import threading

overCardRatio = 1 / 3
globalRatio = 0.8

assert(0 < overCardRatio and overCardRatio <= 1)
assert(0 < globalRatio and globalRatio <= 1)

cardSize = (int(56 * globalRatio), int(109 * globalRatio))

def playerRadius(playerNumber: int) -> float:
    assert(3 <= playerNumber and playerNumber <= 5)
    
    if (playerNumber == 4):
        return 275 * globalRatio
    elif (playerNumber == 3):
        return 225 * globalRatio
    elif (playerNumber == 5):
        return 300 * globalRatio

class TableLabel(kivy.uix.image.Image):
    def __init__(self, image: Image = None):
        super().__init__()
        self.setImage(image)
        self._mousePressPos = None
        self._pressed = False
    
    def setImage(self, image: Image):
        self._image = image
        
        if (image):
            self.img_byte_arr = io.BytesIO()
            image.save(self.img_byte_arr, format='PNG')
            self.img_byte_arr.seek(0)
            self.img = kivy.core.image.Image(self.img_byte_arr, ext="png")
            self.texture = self.img.texture

    def on_touch_up(self, touch):
        super().on_touch_up(touch)
        if (not self._pressed):
            self._mousePressPos = touch
        else:
            self._mousePressPos = None

    def on_touch_down(self, touch):
        super().on_touch_down(touch)
        self._mousePressPos = None
        self._pressed = False

class Window(kivy.uix.gridlayout.GridLayout):
    def __init__(self):
        super().__init__(cols = 2)
        self._playerNumber = 5
        self._window = None
        self._dialog = None
        self._ok = False

        layout = kivy.uix.boxlayout.BoxLayout(orientation = "vertical")

        threeButton = kivy.uix.button.Button(text = "Three players")
        threeButton.bind(on_press = self.threePlayers)
        fourButton = kivy.uix.button.Button(text = "Four players")
        fourButton.bind(on_press = self.fourPlayers)
        fiveButton = kivy.uix.button.Button(text = "Five players")
        fiveButton.bind(on_press = self.fivePlayers)

        layout.add_widget(threeButton)
        layout.add_widget(fourButton)
        layout.add_widget(fiveButton)

        self.add_widget(layout)

    def setOpacity(self, widget, opacity):
        widget.opacity = opacity

    def setSpinnerValues(self, spinner, values):
        spinner.values = values

    def threePlayers(self, instance):
        self._playerNumber = 3
        self.play()

    def fourPlayers(self, instance):
        self._playerNumber = 4
        self.play()

    def fivePlayers(self, instance):
        self._playerNumber = 5
        self.play()

    def displayTable(self, centerCards: list, displayCenterCards: bool = False, centerCardsIsDog: bool = False):
        self._tableLabel.setImage(self._game.tableImage(self._showPlayers, centerCards, displayCenterCards, centerCardsIsDog))

    def comboBoxActivated(self, spinner, text):
        for i in range(0, 6):
            if (self._dogComboBoxes[i] == spinner):
                self._dogIndex = i
                break

    def play(self):
        self._game = Game(self._playerNumber)
        self._game.giveHands()
        self._game._players[0]._isHuman = True
        self._showPlayers = [False for i in range(0, self._playerNumber)]
        self._showPlayers[0] = True #self._showPlayers[random.randrange(self._playerNumber)] = True

        self.clear_widgets()

        self._tableLabel = TableLabel()
        self._pointsLabel = kivy.uix.label.Label(text = "Attack points: 0 - Defence points: 0")
        #self.img = kivy.core.image.Image("images/back.png")
        #self._tableLabel.texture = self.img.texture
        self._contractLabel = kivy.uix.label.Label(text = "Choose a contract")
        self._contractLabel.opacity = 0
        self._contractComboBox = kivy.uix.spinner.Spinner()
        self._contractComboBox.opacity = 0

        choices = []

        for i in range(0, 4):
            choices.append(str(Family(i)))

        self._kingLabel = kivy.uix.label.Label(text = "Call a king")
        self._kingLabel.opacity = 0
        self._kingComboBox = kivy.uix.spinner.Spinner(text = choices[0], values = choices)
        self._kingComboBox.opacity = 0

        self._dogLabel = kivy.uix.label.Label(text = "Do a dog")
        self._dogLabel.opacity = 0
        self._dogComboBoxes = []
        for i in range(0, 6):
            self._dogComboBoxes.append(kivy.uix.spinner.Spinner())
            self._dogComboBoxes[-1].opacity = 0
            self._dogComboBoxes[-1].bind(on_text = self.comboBoxActivated)

        self._cardLabel = kivy.uix.label.Label(text = "Play a card")
        self._cardLabel.opacity = 0
        self._cardComboBox = kivy.uix.spinner.Spinner()
        self._cardComboBox.opacity = 0

        okButton = kivy.uix.button.Button(text = "OK")
        okButton.bind(on_press = self.ok)

        verticalLayout = kivy.uix.boxlayout.BoxLayout(orientation = "vertical")
        verticalLayout.add_widget(self._contractLabel)
        verticalLayout.add_widget(self._contractComboBox)
        verticalLayout.add_widget(self._kingLabel)
        verticalLayout.add_widget(self._kingComboBox)
        verticalLayout.add_widget(self._dogLabel)
        self._dogIndex = 0
        for i in range(0, 6):
            verticalLayout.add_widget(self._dogComboBoxes[i])
        verticalLayout.add_widget(self._cardLabel)
        verticalLayout.add_widget(self._cardComboBox)
        verticalLayout.add_widget(okButton)

        layout = kivy.uix.boxlayout.BoxLayout(orientation = "vertical")

        layout.add_widget(self._tableLabel)
        layout.add_widget(self._pointsLabel)
        self.add_widget(layout)        
        self.add_widget(verticalLayout)

        kivy.clock.Clock.schedule_interval(self.monitor, 10)
        
        self._thread = threading.Thread(target = self._game.play, args = (self, ), daemon = True)
        self._thread.start()

    def ok(self, instance):
        self._ok = True
        
    def monitor(self, dt):
        take = ""
        
        if (self._game._calledKing):
            take = "\nCalled king: " \
                   + str(self._game._calledKing)

        if (self._game._contract):
            take += "\nContract: " \
                    + str(self._game._contract) \
                    + " ({0} points)" \
                    .format(self._game.attackTargetPoints())
    
        self._pointsLabel.text = "Attack points: {0} - Defence points: {1}".format(self._game.attackPoints(), self._game.defencePoints()) + take
                                  
        if (self._tableLabel._mousePressPos):
            for i in range(0, self._game._playerNumber):
                if (i == self._game._currentPlayer):
                    radius = playerRadius(self._game._playerNumber)
                    
                    positions = [(self._tableLabel.pixmap().width() // 2,
                                  self._tableLabel.pixmap().height() // 2 + radius)]
                    angles = [0]

                    for k in range(1, self._playerNumber):
                        angles.append(angles[-1] - 360 / self._playerNumber)
                        x = self._tableLabel.pixmap().width() / 2 + radius * math.sin(math.radians(angles[-1]))
                        y = self._tableLabel.pixmap().height() / 2 + radius * math.cos(math.radians(angles[-1]))
                        positions.append((x, y))

                    n = len(self._game._players[i]._cards)
                    w = (n - 1) * cardSize[0] * overCardRatio + cardSize[0]

                    for j in range(0, n):
                        rect = QRectF(int(j * cardSize[0] * overCardRatio), 0, cardSize[0] * (1 if j == n - 1 else overCardRatio), cardSize[1])
                        transform = QTransform()
                        transform.translate(rect.center().x(), rect.center().y())
                        transform.rotate(angles[i])
                        transform.translate(-rect.center().x(), -rect.center().y())
                        transform.translate(positions[i][0] - w / 2,
                                            positions[i][1] - cardSize[1] / 2)
        
                        points = [transform.map(rect.topLeft()),
                                  transform.map(rect.topRight()),
                                  transform.map(rect.bottomRight()),
                                  transform.map(rect.bottomLeft()),
                                  transform.map(rect.topLeft())]
                        
                        polygon = QPolygonF(points)
                       
                        if (polygon.containsPoint(self._tableLabel._mousePressPos, Qt.WindingFill)):
                            enabledCards = []
                        
                            enabledCards = self._game._players[i].enabledCards(self._game._centerCards,
                                                                               self._game._firstRound,
                                                                               self._game._calledKing,
                                                                               self._dogLabel.isVisible())

                            if (enabledCards[j]):
                                if (self._cardComboBox.isVisible()):
                                    self._cardComboBox.setCurrentText(self._game._players[i]._cards[j].name())
                                elif (self._dogLabel.isVisible()):
                                    self._tableLabel._mousePressPos = None
                                    self._dogComboBoxes[self._dogIndex].setCurrentText(self._game._players[i]._cards[j].name())
                                    self._dogIndex += 1
                                    if (not self._dogComboBoxes[self._dogIndex].isVisible()):
                                        self._dogIndex = 0
                            
                            break

                    break
    
        if (not self._thread.is_alive()):
            if (self._game.attackPoints() == 0
                and self._game.defencePoints() == 0):
                QMessageBox.information(self._window,
                                        "Game over",
                                        "Nobody takes!")
                
                self._window.close()
            else:
                if (self._game.attackWins()):
                     QMessageBox.information(self._window,
                                             "Game over",
                                             "Attack wins ({0} points for {1} points)!"
                                             .format(self._game.attackPoints(),
                                                     self._game.attackTargetPoints()))
                else:
                     QMessageBox.information(self._window,
                                             "Game over",
                                             "Attack loses ({0} points for {1} points)!"
                                             .format(self._game.attackPoints(),
                                                     self._game.attackTargetPoints()))
                
                self._window.close()

class App(kivy.app.App):
    def build(self):
        return Window()

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
            return "Fool"
            
        return "Asset {0}".format(self.value())

    def imageName(self) -> str:
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
    
    def name(self) -> str:
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

    def __str__(self) -> str:
        return self.name()

class Family(Enum):
    Heart = 0
    Diamond = 1
    Club = 2
    Spade = 3

    def __int__(self) -> int:
        return self.value
    
    def name(self) -> str:
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

    def __str__(self) -> str:
        return self.name()

class Head(Enum):
    Jack = 0
    Knight = 1
    Queen = 2
    King = 3

    def __int__(self) -> int:
        return self.value
    
    def name(self) -> str:
        if (self.value == 0):
            return "Jack"
        elif (self.value == 1):
            return "Knight"
        elif (self.value == 2):
            return "Queen"
        elif (self.value == 3):
            return "King"
        else:
            return ""

    def __str__(self) -> str:
        return self.name()

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

        if (self.value() == 1):
            if (self._family == Family.Heart):
                s = "Ace of hearts"
            elif (self._family == Family.Diamond):
                s = "Ace of diamonds"
            elif (self._family == Family.Club):
                s = "Ace of clubs"
            elif (self._family == Family.Spade):
                s = "Ace of spade"
        elif (self.value() <= 10):
            if (self._family == Family.Heart):
                s = "Heart {0}".format(self.value())
            elif (self._family == Family.Diamond):
                s = "Diamond {0}".format(self.value())
            elif (self._family == Family.Club):
                s = "Club {0}".format(self.value())
            elif (self._family == Family.Spade):
                s = "Spade {0}".format(self.value())
        elif (self.value() == 11):
            if (self._family == Family.Heart):
                s = "Heart jack"
            elif (self._family == Family.Diamond):
                s = "Diamond jack"
            elif (self._family == Family.Club):
                s = "Club jack"
            elif (self._family == Family.Spade):
                s = "Spade jack"
        elif (self.value() == 12):
            if (self._family == Family.Heart):
                s = "Heart knight"
            elif (self._family == Family.Diamond):
                s = "Diamond knight"
            elif (self._family == Family.Club):
                s = "Club knight"
            elif (self._family == Family.Spade):
                s = "Spade knight"
        elif (self.value() == 13):
            if (self._family == Family.Heart):
                s = "Heart queen"
            elif (self._family == Family.Diamond):
                s = "Diamond queen"
            elif (self._family == Family.Club):
                s = "Club queen"
            elif (self._family == Family.Spade):
                s = "Spade queen"
        else: #elif (self.value() == 14):
            if (self._family == Family.Heart):
                s = "Heart king"
            elif (self._family == Family.Diamond):
                s = "Diamond king"
            elif (self._family == Family.Club):
                s = "Club king"
            elif (self._family == Family.Spade):
                s = "Spade king"

        return s

    def imageName(self) -> str:
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
            return int(self._head) + 1 + 0.5

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

    def image(self):
        image = Image.open("images/" + self.imageName() + ".png")

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

def imageForCards(cards: list, enabledCards: list, shown: bool = True):
    assert(len(cards) == len(enabledCards))

    if (len(cards) == 0):
        return None
    
    firstImage = None
    
    if (shown):
        firstImage = cards[0].image()
    else:
        firstImage = Image.open("images/back.png")
        
        firstImage = firstImage.resize(cardSize)
    
    image = Image.new('RGBA', (firstImage.width + int((len(cards) - 1) * firstImage.width * overCardRatio), firstImage.height))
    
    for i in range(0, len(cards)):
        im = None
        
        if (shown):
            im = cards[i].image()
        else:
            im = firstImage
            
        image.paste(im, (int(i * firstImage.width * overCardRatio), 0))
        
        if (shown):
            if (not enabledCards[i]):
                im = Image.new('RGBA', (im.width, im.height))
                im.paste((0, 0, 0, 128), [0, 0, im.width, im.height])
                img = Image.new('RGBA', (image.width, image.height))
                img.paste(im, (int(i * firstImage.width * overCardRatio), 0))
                image = Image.alpha_composite(image, img)
    
    return image

def pointsForCards(cards: list) -> int:
    points = 0
    
    for card in cards:
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
        
        points += pointsForCards(self._folds)

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

    def chooseContract(self, window: Window, contract: Contract) -> Contract:
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
            kivy.clock.Clock.schedule_once(lambda dt: window.setOpacity(window._contractLabel, 1), 0)
            kivy.clock.Clock.schedule_once(lambda dt: window.setSpinnerValues(window._contractComboBox, choices), 0)
            kivy.clock.Clock.schedule_once(lambda dt: window.setOpacity(window._contractComboBox, 1), 0)
            window._ok = False
            
            while (not window._ok):
                time.sleep(0.01)
            
            contract = {v: k for k, v in strContracts.items()}.get(choices[window._contractComboBox.currentIndex()])
            
            kivy.clock.Clock.schedule_once(lambda dt: window.setOpacity(window._contractLabel, 0), 0)
            kivy.clock.Clock.schedule_once(lambda dt: window.setOpacity(window._contractComboBox, 0), 0)

            if (contract == -1):
                return None
            else:
                return Contract(contract)
        else:
            #TODO: ...
            
            return None
    
    def callKing(self, window: Window) -> Family:
        strFamilies = {}
        choices = []
        
        for i in range(0, 4):
            strFamilies[i] = str(Family(i))
            choices.append(str(Family(i)))
        
        calledKing = None
        
        if (self._isHuman):
            kivy.clock.Clock.schedule_once(lambda dt: window.setOpacity(window._kingLabel, 1), 0)
            kivy.clock.Clock.schedule_once(lambda dt: window.setOpacity(window._kingComboBox, 1), 0)
            window._ok = False
            
            while (not window._ok):
                time.sleep(0.01)
            
            calledKing = {v: k for k, v in strFamilies.items()}.get(choices[window._kingComboBox.currentIndex()])
            
            kivy.clock.Clock.schedule_once(lambda dt: window.setOpacity(window._kingLabel, 0), 0)
            kivy.clock.Clock.schedule_once(lambda dt: window.setOpacity(window._kingComboBox, 0), 0)
        else:
            #TODO: ...
            
            pass

        return Family(calledKing)
    
    def doDog(self, dog: list, window: Window) -> list:
        newDog = []
        
        self._cards += dog
        self._cards = sortCards(self._cards)
        
        window.displayTable([], False, True)

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
            
            kivy.clock.Clock.schedule_once(lambda dt: window.setOpacity(window._dogLabel, 1), 0)
            
            for i in range(0, len(dog)):
                kivy.clock.Clock.schedule_once(lambda dt: window.setSpinnerValues(window._dogComboBoxes[i], choices), 0)
                kivy.clock.Clock.schedule_once(lambda dt: window.setOpacity(window._dogComboBoxes[i], 1), 0)

            loop = True
            
            while (loop):
                window._ok = False
                
                while (not window._ok):
                    time.sleep(0.01)
  
                selectedCards = []
                
                for i in range(0, len(dog)):
                    selectedCards.append(choices[window._dogComboBoxes[i].currentIndex()])
                
                loop = len(set(selectedCards)) != len(dog)
            
            kivy.clock.Clock.schedule_once(lambda dt: window.setOpacity(window._dogLabel, 0), 0)
            
            for i in range(0, len(dog)):
                kivy.clock.Clock.schedule_once(lambda dt: window.setOpacity(window._dogComboBoxes[i], 0), 0)
                          
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

    def enabledCards(self, cards: list, firstRound: bool, calledKing: Family, doDog = False):
        enabledCards = []
        
        if (doDog):
            for i in range(0, len(self._cards)):
                if (not (self._cards[i].isAsset()
                         or (self._cards[i].isFamilyCard()
                         and self._cards[i].familyCard().value() == 14))):
                        enabledCards.append(True)
                else:
                    enabledCards.append(False)
            
            return enabledCards
    
        cardAssets = []

        for card in cards:
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
            
            ok = True
            
            if (firstRound):
                if (len(cards) == 0):
                    if (self._cards[i].isFamilyCard()
                        and self._cards[i].familyCard().family() == calledKing
                        and self._cards[i].familyCard().value() != 14):
                        add = False
                        ok = False
                else:
                    ok = True
            
            if (ok):
                firstCard = None
            
                if (len(cards)):
                    firstCard = cards[0]
                    
                    if (firstCard.isAsset() and firstCard.asset().isFool()):
                        if (len(cards) > 1):
                            firstCard = cards[1]
                        else:
                            firstCard = None

                if (firstCard):
                    if (firstCard.isAsset()):
                        if (len(handAssets)):
                            if (self._cards[i].isAsset()):
                                if (not self._cards[i].asset().isFool()
                                    and handAssets[-1].value() > cardAssets[-1].value()
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
            
            enabledCards.append(add)

        return enabledCards

    def playCard(self, cards: dict, firstRound: bool, calledKing: Family) -> Card:
        time.sleep(1)

        card = None

        cardList = [x[1] for x in cards.items()]
        
        enabledCards = self.enabledCards(cardList, firstRound, calledKing)
        
        strCards = {}
        choices = []

        for i in range(0, len(enabledCards)):
            if (enabledCards[i]):
                strCards[i] = self._cards[i].name()
                choices.append(self._cards[i].name())

        window.displayTable(cardList, True)

        if (self._isHuman):
            kivy.clock.Clock.schedule_once(lambda dt: window.setOpacity(window._cardLabel, 1), 0)
            kivy.clock.Clock.schedule_once(lambda dt: window.setSpinnerValues(window._cardComboBox, choices), 0)
            kivy.clock.Clock.schedule_once(lambda dt: window.setOpacity(window._cardComboBox, 1), 0)
            window._ok = False
            
            while (not window._ok):
                time.sleep(0.01)
            
            kivy.clock.Clock.schedule_once(lambda dt: window.setOpacity(window._cardLabel, 0), 0)
            kivy.clock.Clock.schedule_once(lambda dt: window.setOpacity(window._cardComboBox, 0), 0)
            
            selectedCard = {v: k for k, v in strCards.items()}.get(choices[window._cardComboBox.currentIndex()])

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
        self._currentPlayer = None
        self._firstRound = True
        self._centerCards = []
        assert(3 <= self._playerNumber and self._playerNumber <= 5)
    
    def play(self, window: Window):
        self._firstPlayer = random.randrange(self._playerNumber)
        
        for i in range(0, self._playerNumber):
            p = (self._firstPlayer + i) % self._playerNumber
            self._currentPlayer = p
            window.displayTable(self._dog, False, True)
            contract = self._players[p].chooseContract(window, self._contract)
            if (contract):
                self._taker = p
                self._contract = contract
        
        if (not self._contract):
            return

        self._players[self._taker]._attackTeam = True
        self._players[self._taker]._teamKnown = True

        self._currentPlayer = self._taker
        window.displayTable(self._dog, False, True)

        if (self._playerNumber == 5):
            self._calledKing = self._players[self._taker].callKing(window)
        else:
            for i in range(0, len(self._players)):
                if (i != self._taker):
                    self._players[i]._attackTeam = False
                    self._players[i]._teamKnown = True

        if (self._contract == Contract.Little
            or self._contract == Contract.Guard):
            window.displayTable(self._dog, True, True)
            time.sleep(1)

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
                        self._players[i]._teamKnown = True

            self._dog = self._players[self._taker].doDog(self._dog, window)

        n = (78 - len(self._dog)) // self._playerNumber

        for i in range(0, n):
            cards = {}

            for j in range(0, self._playerNumber):
                self._centerCards = []
                p = (self._firstPlayer + j) % self._playerNumber
                self._currentPlayer = p
                self._firstRound = (i == 0)
                cards[p] = self._players[p].playCard(cards, self._firstRound, self._calledKing)
                self._centerCards = [x[1] for x in cards.items()]
                
                if (cards[p].isFamilyCard()
                    and cards[p].familyCard().family() == self._calledKing
                    and cards[p].familyCard().value() == 14):
                    self._players[p]._attackTeam = True
                    
                    for player in self._players:
                        player._teamKnown = True
                    
                if (not self._players[p]._teamKnown):
                    firstCard = None
                        
                    if (len(cards)):
                        firstCard = list(cards.items())[0][1]
                        
                        if (firstCard.isAsset()
                            and firstCard.asset().isFool()):
                            if (len(list(cards.items())) > 1):
                                firstCard = None
                            else:
                                firstCard = list(cards.items())[1][1]
                                    
                    if (cards[p].isAsset()):      
                        if (firstCard and firstCard.isFamilyCard()
                            and firstCard.familyCard().family() == self._calledKing):
                            self._players[p]._attackTeam = False
                            self._players[p]._teamKnown = True
                    elif (cards[p].isFamilyCard()
                          and firstCard == self._calledKing
                          and cards[p].isFamilyCard() != self._calledKing):
                        self._players[p]._attackTeam = False
                        self._players[p]._teamKnown = True

                window.displayTable([v for k, v in cards.items()], True)
                time.sleep(1)
            
            self._firstPlayer = self.playSet(cards, i == n - 1)

        window.displayTable(self._dog, True)
        time.sleep(1)

        if (self._contract == Contract.GuardWithout):
            for p in self._players:
                if (p.defenceTeam()):
                    p._folds += self._dog
                    break
        else:
            self._players[self._taker]._folds += self._dog

        self._dog = []
        
        window.displayTable([])
        
        self._currentPlayer = None

    def attackPoints(self):
        points = 0

        for p in self._players:
            if p.teamKnown() and p.attackTeam():
                points += p.points()

        return points

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
        self._firstRound = True
        self._centerCards = []
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
        
        n = 78 // 3 // self._playerNumber
        
        for i in range(0, n):
            for j in range(0, len(self._players)):
                self._players[j]._cards += self._cards[0:3]
                self._cards = self._cards[3:]
        
        for player in self._players:
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
                                self._players[i]._folds.append(list(assets.items())[foolIndex][1])
                                del assets[i]
                                break
                    else:
                        for i in range(0, self.playerNumber):
                            if (self._players[i].attackTeam()):
                                self._players[i]._folds.append(list(assets.items())[foolIndex][1])
                                del assets[i]
                                break
                else:
                    self._players[p]._folds.append(list(assets.items())[foolIndex][1])
                    del assets[p]
                    
            if (len(assets)):
                p = list(assets.items())[-1][0]
                self._players[p]._folds += [x[1] for x in cards.items()]
                return p
        
        firstCard = list(cards.items())[0][1]
        
        if (firstCard.isAsset() and firstCard.asset().isFool()):
            firstCard = list(cards.items())[1][1]
        
        f = firstCard.familyCard().family()
        p = list(families[f].items())[-1][0]
        self._players[p]._folds += [x[1] for x in cards.items()]
        
        self.giveFoolCard()
        
        return p

    def attackTargetPoints(self):
        points = 56
        oudlerCount = countOudlersForCards(self.attackFolds())

        if (oudlerCount == 3):
            points = 36
        elif (oudlerCount == 2):
            points = 41
        elif (oudlerCount == 1):
            points = 51
            
        return points

    def defenceTargetPoints(self):
        points = 56
        oudlerCount = countOudlersForCards(self.defencefolds())

        if (oudlerCount == 3):
            points = 36
        elif (oudlerCount == 2):
            points = 41
        elif (oudlerCount == 1):
            points = 51
            
        return points

    def attackWins(self):
        return self.attackPoints() >= self.attackTargetPoints()

    def defenceWins(self):
        return not self.attackWins()

    def tableImage(self, showPlayers: list, centerCards: list, showCenterCards: bool, centerCardsIsDog: bool = False):
        assert(len(showPlayers) == self._playerNumber)
        
        tableImage = Image.new('RGBA', (int(1024 * globalRatio), int(768 * globalRatio)), color=(139, 69, 19))
        
        centerCardsImage = imageForCards(centerCards, [True for c in centerCards], shown = showCenterCards)
        
        if (centerCardsImage):
            tableImage.paste(centerCardsImage, (int((tableImage.width - centerCardsImage.width) / 2),
                                                int((tableImage.height - centerCardsImage.height) / 2)))
        
        radius = playerRadius(self._playerNumber)
        
        positions = [(tableImage.width // 2,
                      tableImage.height // 2 + radius)]
        angles = [0]

        for i in range(1, self._playerNumber):
            angles.append(angles[-1] - 360 / self._playerNumber)
            x = tableImage.width / 2 + radius * math.sin(math.radians(angles[-1]))
            y = tableImage.height / 2 + radius * math.cos(math.radians(angles[-1]))
            positions.append((x, y))

        for i in range(0, self._playerNumber):
            text = "?"
            
            if (self._players[i].teamKnown()):
                text = "Attack" if self._players[i].attackTeam() else "Defence"
        
            draw = ImageDraw.Draw(tableImage)
        
            font = ImageFont.truetype("DejaVuSans.ttf", 20)
            bbox = draw.textbbox((0, 0), text, font = font, spacing = 0, align = "center")
            w = bbox[2] - bbox[0]
            h = int(1.5 * (bbox[3] - bbox[1]))
            textImage = Image.new('RGBA', (w, h))
            draw = ImageDraw.Draw(textImage)
            draw.text((0, 0), text, font = font, fill = "black")
            textImage = textImage.resize((int(textImage.width * globalRatio),
                                          int(textImage.height * globalRatio)))
            textImage = textImage.rotate(angles[i], expand = True)
            
            x = positions[i][0]
            y = positions[i][1]

            image = Image.new('RGBA', (tableImage.width, tableImage.height))
            image.paste(textImage, (int(x - globalRatio * 80 * math.sin(math.radians(angles[i])) - textImage.width / 2),
                                    int(y - globalRatio * 80 * math.cos(math.radians(angles[i])) - textImage.height / 2)))
            tableImage = Image.alpha_composite(tableImage, image)
            
            enabledCards = self._players[i].enabledCards(centerCards, self._firstRound, self._calledKing, centerCardsIsDog)

            playerCardsImage = imageForCards(self._players[i]._cards,
                                             enabledCards,
                                             shown = showPlayers[i])
            
            if (playerCardsImage):
                img = playerCardsImage

                if (i == self._currentPlayer):
                    bgImg = img.resize((int(img.width + 10 * globalRatio),
                                        int(img.height + 10 * globalRatio)))
                    bgImg.paste((255, 255, 0, 128), [0, 0, bgImg.width, bgImg.height])
                    bgImg = bgImg.rotate(angles[i], expand = True)
                    
                    image = Image.new('RGBA', (tableImage.width, tableImage.height))
                    image.paste(bgImg, (int(x - bgImg.width / 2),
                                        int(y - bgImg.height / 2)))
                    tableImage = Image.alpha_composite(tableImage, image)    

                img = img.rotate(angles[i], expand = True)
                x -= img.width / 2
                y -= img.height / 2
                image = Image.new('RGBA', (tableImage.width, tableImage.height))
                image.paste(img, (int(x), int(y)))
                tableImage = Image.alpha_composite(tableImage, image)

        return tableImage

app = App()
app.run()
