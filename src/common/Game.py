from common import Asset
from common import Card
from common import Contract
from common import Family
from common import FamilyCard
from common import Head
from common import Player
from common import common
from enum import Enum
import math
import os
from PIL import Image, ImageDraw, ImageFont
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QTransform
from PyQt5 import QtTest
import random
from server import Server

class GameState(Enum):
    Begin = 0
    ChooseContract = 1
    CallKing = 2
    ShowDog = 3
    DoDog = 4
    Play = 5
    End = 6

class GameData:
    def __init__(self, playerNumber: int):
        assert(3 <= playerNumber and playerNumber <= 5)
        
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
        self._gameState = GameState.Begin
        self._remainingTime = 0

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
        
        for i in range(0, self._playerNumber):
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
        
        folds = sorted(folds, key = lambda x: x.points())
            
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
        self._gameState = GameState.Begin
        self._foolPlayed = None
        self._foolCardGiven = False
        self._cards = []
        self._firstRound = True
        self._centerCards = []
        self._firstPlayer = random.randrange(self._playerNumber)
        for i in range(0, 4):
            for j in range(1, 11):
                self._cards.append(Card.Card(familyCard = FamilyCard.FamilyCard(family = Family.Family(i), value = j)))
            for j in range(0, 4):
                self._cards.append(Card.Card(familyCard = FamilyCard.FamilyCard(family = Family.Family(i), head = Head.Head(j))))
        for i in range(0, 22):
            self._cards.append(Card.Card(asset = Asset.Asset(i)))
        random.shuffle(self._cards)
        assert(len(self._cards) == 78)
        
        self._players = [Player.Player() for i in range(0, self._playerNumber)]
        
        n = 78 // 3 // self._playerNumber
        
        for i in range(0, n):
            for j in range(0, len(self._players)):
                self._players[j]._cards += self._cards[0:3]
                self._cards = self._cards[3:]
        
        for player in self._players:
            player._cards = common.sortCards(player._cards)
        
        self._dog = common.sortCards(self._cards)
        self._cards = []
        
        for player in self._players:
            assets = []
            
            for card in player._cards:
                if (card.isAsset()):
                    assets.append(card)
                    
            if (len(assets) == 1 and assets[0].value() == 1):
                self.giveHands()

    def setWinner(self, cards: dict):
        if (len(cards) == 0):
            return (None, None)
            
        assets = {}
        families = {Family.Family.Heart: {},
                    Family.Family.Diamond: {},
                    Family.Family.Club: {},
                    Family.Family.Spade: {}}
        for k, v in cards.items():
            if v.isAsset():
                assets[k] = v
            else: #elif v.isFamilyCard():
                families[v.familyCard().family()][k] = v
        
        if (len(assets)):
            assets = dict(sorted(assets.items(), key = lambda item: item[1].value()))
            
            p, a = list(assets.items())[-1]
            
            if (a.value() > 0):
                return (p, a)
                
        p, firstCard = list(cards.items())[0]
        
        if (firstCard.isAsset() and firstCard.asset().isFool()):
            if (len(cards) > 1):
                p, firstCard = list(cards.items())[1]
            else:
                return (p, firstCard)
                
        f = dict(sorted(families[firstCard.familyCard().family()].items(), key = lambda item: item[1].value()))
        
        p, c = list(f.items())[-1]
        
        return (p, c)
    
    def playSet(self, cards: dict, lastSet: bool):
        assets = {}
        families = {Family.Family.Heart: {},
                    Family.Family.Diamond: {},
                    Family.Family.Club: {},
                    Family.Family.Spade: {}}
        for k, v in cards.items():
            if v.isAsset():
                assets[k] = v
            else: #elif v.isFamilyCard():
                families[v.familyCard().family()][k] = v.familyCard()

        assets = dict(sorted(assets.items(), key = lambda x: x[1].value()))
        for i in range(0, 4):
            families[Family.Family(i)] = dict(sorted(families[Family.Family(i)].items(), key = lambda x: x[1].value()))

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
                                del assets[list(assets.keys())[foolIndex]]
                                break
                    else:
                        for i in range(0, self._playerNumber):
                            if (self._players[i].attackTeam()):
                                self._players[i]._folds.append(list(assets.items())[foolIndex][1])
                                del assets[list(assets.keys())[foolIndex]]
                                break
                else:
                    self._players[p]._folds.append(list(assets.items())[foolIndex][1])
                    del assets[list(assets.keys())[foolIndex]]
                    
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
        oudlerCount = common.countOudlersForCards(self.attackFolds())

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

    def tableImage(self, gui, showPlayers: list, centerCards: list, showCenterCards: bool, centerCardsIsDog: bool = False, bottomPlayer: int = 0):
        assert(len(showPlayers) == self._playerNumber)
        
        tableImage = Image.new('RGBA', (int(1025 * 0.86), int(700 * 0.86)), color=(139, 69, 19))
        
        centerCardsImage = common.imageForCards(centerCards, [True for c in centerCards], gui._cardSize, gui._overCardRatio, shown = showCenterCards)
        
        if (centerCardsImage):
            tableImage.paste(centerCardsImage, (int((tableImage.width - centerCardsImage.width) / 2),
                                                int((tableImage.height - centerCardsImage.height) / 2)))
        
        radius = common.playerRadius(self._playerNumber, gui._globalRatio)
        
        positions = [(tableImage.width // 2,
                      tableImage.height // 2 + radius)]
        angles = [0]

        for i in range(1, self._playerNumber):
            angles.append(angles[-1] - 360 / self._playerNumber)
            x = tableImage.width / 2 + radius * math.sin(math.radians(angles[-1]))
            y = tableImage.height / 2 + radius * math.cos(math.radians(angles[-1]))
            positions.append((x, y))

        for j in range(0, self._playerNumber):
            i = (bottomPlayer + j) % self._playerNumber

            x = positions[j][0]
            y = positions[j][1]

            avatarCenter = (int(x - gui._globalRatio * 120 * math.sin(math.radians(angles[j]))),
                            int(y - gui._globalRatio * 120 * math.cos(math.radians(angles[j]))))

            if (self._players[i]._avatar):
                img = common.intRoundImage(self._players[i]._avatar)
                size = (32, 32)

                if (not img):
                    img = Image.new('RGBA', size)
                
                img = img.resize(size)
                img = img.rotate(angles[j], expand = True)

                image = Image.new('RGBA', (tableImage.width, tableImage.height))
                image.paste(img, (avatarCenter[0] - img.width // 2,
                                  avatarCenter[1] - img.height // 2))
                tableImage = Image.alpha_composite(tableImage, image)

            if (i == self._currentPlayer):
                draw = ImageDraw.Draw(tableImage)
                draw.arc((avatarCenter[0] - img.width // 2,
                          avatarCenter[1] - img.height // 2,
                          avatarCenter[0] + img.width // 2,
                          avatarCenter[1] + img.height // 2),
                          start = -self._remainingTime / 30 * 360 + -90,
                          end = -90,
                          fill = "green", width = 2)

            transform = QTransform()
            transform.translate(tableImage.width / 2, tableImage.height / 2)
            transform.rotate(-angles[j])

            if (self._players[i].teamKnown()):
                img = Image.open(os.path.dirname(__file__) + "/../../images/shield.png")

                if (self._players[i].attackTeam()):
                    if (i == self._taker):
                        img = Image.open(os.path.dirname(__file__) + "/../../images/swords.png")
                    else:
                        img = Image.open(os.path.dirname(__file__) + "/../../images/sword.png")

                img = common.extRoundImage(img, (255, 255, 255, 255))

                size = (16, 16)
                img = img.resize(size)
                img = img.rotate(angles[j], expand = True)

                image = Image.new('RGBA', (tableImage.width, tableImage.height))
                p = transform.map(16,
                                  radius - gui._globalRatio * 120 - 16)
                image.paste(img, (int(p[0] - img.width // 2),
                                  int(p[1] - img.height // 2)))
                tableImage = Image.alpha_composite(tableImage, image)

            if (i == self._taker and self._calledKing):
                img = Image.open(os.path.dirname(__file__) + "/../../images/"
                                 + self._calledKing.imageName() + ".png")

                img = common.extRoundImage(img, (255, 255, 255, 255))

                size = (16, 16)
                img = img.resize(size)
                img = img.rotate(angles[j], expand = True)

                image = Image.new('RGBA', (tableImage.width, tableImage.height))
                p = transform.map(16,
                                  radius - gui._globalRatio * 120 + 16)
                image.paste(img, (int(p[0] - img.width // 2),
                                  int(p[1] - img.height // 2)))
                tableImage = Image.alpha_composite(tableImage, image)

            text = self._players[i]._name
            draw = ImageDraw.Draw(tableImage)
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
            bbox = draw.textbbox((0, 0), text, font = font, spacing = 0, align = "center")
            w = bbox[2] - bbox[0]
            h = int(1.5 * (bbox[3] - bbox[1]))
            textImage = Image.new('RGBA', (w, h))
            draw = ImageDraw.Draw(textImage)
            draw.text((0, 0), text, font = font, fill = "white")
            textImage = textImage.resize((int(textImage.width * gui._globalRatio),
                                          int(textImage.height * gui._globalRatio)))
            textImage = textImage.rotate(angles[j], expand = True)
            
            image = Image.new('RGBA', (tableImage.width, tableImage.height))
            image.paste(textImage, (int(x - gui._globalRatio * 80 * math.sin(math.radians(angles[j])) - textImage.width / 2),
                                    int(y - gui._globalRatio * 80 * math.cos(math.radians(angles[j])) - textImage.height / 2)))
            tableImage = Image.alpha_composite(tableImage, image)
            
            text = str(self._players[i].points())
            draw = ImageDraw.Draw(tableImage)
            font = ImageFont.truetype("DejaVuSans.ttf", 14)
            bbox = draw.textbbox((0, 0), text, font = font, spacing = 0, align = "center")
            w = bbox[2] - bbox[0]
            h = int(1.5 * (bbox[3] - bbox[1]))
            textImage = Image.new('RGBA', (w, h))
            draw = ImageDraw.Draw(textImage)
            draw.text((0, 0), text, font = font, fill = "white")
            textImage = textImage.resize((int(textImage.width * gui._globalRatio),
                                          int(textImage.height * gui._globalRatio)))
            textImage = textImage.rotate(angles[j], expand = True)
            
            image = Image.new('RGBA', (tableImage.width, tableImage.height))
            p = transform.map(-16,
                              radius - gui._globalRatio * 120 + 16)
            image.paste(textImage, (int(p[0] - textImage.width // 2),
                                    int(p[1] - textImage.height // 2)))
            tableImage = Image.alpha_composite(tableImage, image)

            text = "H" if self._players[i].isHuman() else "B" #Human or Bot
            draw = ImageDraw.Draw(tableImage)
            font = ImageFont.truetype("DejaVuSans.ttf", 14)
            bbox = draw.textbbox((0, 0), text, font = font, spacing = 0, align = "center")
            w = bbox[2] - bbox[0]
            h = int(1.5 * (bbox[3] - bbox[1]))
            textImage = Image.new('RGBA', (w, h))
            draw = ImageDraw.Draw(textImage)
            draw.text((0, 0), text, font = font, fill = "white")
            textImage = textImage.resize((int(textImage.width * gui._globalRatio),
                                          int(textImage.height * gui._globalRatio)))
            textImage = textImage.rotate(angles[j], expand = True)

            image = Image.new('RGBA', (tableImage.width, tableImage.height))
            p = transform.map(-16,
                              radius - gui._globalRatio * 120 - 16)
            image.paste(textImage, (int(p[0] - textImage.width // 2),
                                    int(p[1] - textImage.height // 2)))
            tableImage = Image.alpha_composite(tableImage, image)
            
            enabledCards = self._players[i].enabledCards(centerCards, self._firstRound, self._calledKing, centerCardsIsDog)

            playerCardsImage = common.imageForCards(self._players[i]._cards,
                                                    enabledCards,
                                                    gui._cardSize, gui._overCardRatio, 
                                                    shown = showPlayers[i])
            
            if (playerCardsImage):
                img = playerCardsImage

                if (i == self._currentPlayer):
                    bgImg = img.resize((int(img.width + 10),
                                        int(img.height + 10)))
                    bgImg.paste((255, 255, 0, 128), [0, 0, bgImg.width, bgImg.height])
                    bgImg = bgImg.rotate(angles[j], expand = True)
                    
                    image = Image.new('RGBA', (tableImage.width, tableImage.height))
                    image.paste(bgImg, (int(x - bgImg.width / 2),
                                        int(y - bgImg.height / 2)))
                    tableImage = Image.alpha_composite(tableImage, image)    

                img = img.rotate(angles[j], expand = True)
                x -= img.width / 2
                y -= img.height / 2
                image = Image.new('RGBA', (tableImage.width, tableImage.height))
                image.paste(img, (int(x), int(y)))
                tableImage = Image.alpha_composite(tableImage, image)

        return tableImage

    def playedCards(self):
        assets = []
        families = {Family.Family.Heart: [],
                    Family.Family.Diamond: [],
                    Family.Family.Club: [],
                    Family.Family.Spade: []}

        folds = self.attackFolds() + self.defenceFolds()
                    
        for c in folds:
            if c.isAsset():
                assets.append(c)
            else: #elif c.isFamilyCard():
                families[c.familyCard().family()].append(c)
        
        assets = sorted(assets, key = lambda x: x.value())
        
        for k, v in families.items():
            families[k] = sorted(families[k], key = lambda x: x.value())
        
        return (assets, families)

class Game(GameData):
    def __init__(self, server: Server.Server, playerNumber: int = 5):
        super().__init__(playerNumber)
        self._server = server

    def play(self):
        self._firstPlayer = random.randrange(self._playerNumber)
        
        self._gameState = GameState.Begin
        
        for i in range(0, self._playerNumber):
            p = (self._firstPlayer + i) % self._playerNumber
            self._currentPlayer = p

            self._state = GameState.ChooseContract
            contract = self._server.chooseContract(self)
            if (contract):
                self._taker = p
                self._contract = contract
        
        if (not self._contract):
            self._gameState = GameState.ShowDog
            QtTest.QTest.qWait(1000)

            self._gameState = GameState.End

            return

        self._players[self._taker]._attackTeam = True
        self._players[self._taker]._teamKnown = True

        self._currentPlayer = self._taker
        self._gameState = GameState.CallKing

        if (self._playerNumber == 5):
            self._calledKing = self._server.callKing(self)
        else:
            for i in range(0, len(self._players)):
                if (i != self._taker):
                    self._players[i]._attackTeam = False
                    self._players[i]._teamKnown = True

        kingInDog = False

        if (self._contract == Contract.Contract.Little
            or self._contract == Contract.Contract.Guard):
            self._gameState = GameState.ShowDog
            QtTest.QTest.qWait(2000)

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

        if (self._contract == Contract.Contract.Little
            or self._contract == Contract.Contract.Guard):
            self._gameState = GameState.DoDog
        
            self._dog = self._server.doDog(self)

        self._gameState = GameState.Play
        
        n = (78 - len(self._dog)) // self._playerNumber

        for i in range(0, n):
            cards = {}

            players = [(self._firstPlayer + j) % self._playerNumber for j in range(0, self._playerNumber)]

            for j in range(0, self._playerNumber):
                self._centerCards = []
                p = (self._firstPlayer + j) % self._playerNumber
                self._currentPlayer = p
                self._firstRound = (i == 0)
                cards[p] = self._server.playCard(self)
                self._centerCards = [x[1] for x in cards.items()]
                
                if (cards[p].isFamilyCard()
                    and cards[p].familyCard().family() == self._calledKing
                    and cards[p].familyCard().value() == 14):
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

                QtTest.QTest.qWait(1000)
            
            self._firstPlayer = self.playSet(cards, i == n - 1)

        self._gameState = GameState.ShowDog
        QtTest.QTest.qWait(1000)

        if (self._contract == Contract.Contract.GuardWithout):
            for p in self._players:
                if (p.defenceTeam()):
                    p._folds += self._dog
                    break
        else:
            self._players[self._taker]._folds += self._dog

        self._dog = []
        
        self._currentPlayer = None
        self._gameState = GameState.End
