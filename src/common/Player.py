from common import Card
from common import Contract
from common import Family
from common import common
import os
from PIL import Image
from PyQt5.QtCore import QCoreApplication
from PyQt5 import QtTest
import random

class Player:
    def __init__(self):
        names = ["Paul", "Cathy", "Hector", "Samuel", "Nicolas", "Anne",
                 "Hermine", "Marie", "Joseph", "Marion", "Julien",
                 "Benjamin", "Claire", "François", "Laurence",
                 "Claude", "Jean", "Laure", "Faustine", "Sophie",
                 "Camille", "Arnaud", "Geoffrey", "Aurélie",
                 "Laura", "Pierre", "Simon"]

        self._name = names[random.randrange(len(names))]
        self._avatar = Image.open(os.path.dirname(__file__) + "/../../images/avatar.png")
        self._connected = True
        self._idle = False
        self._folds = []
        self._cards = []
        self._attackTeam = False
        self._teamKnown = False
        self._isHuman = False
        self._cuts = {Family.Family.Heart: False,
                      Family.Family.Diamond: False,
                      Family.Family.Club: False,
                      Family.Family.Spade: False}

    def isHuman(self):
        return self._isHuman

    def points(self) -> int:
        points = 0

        points += common.pointsForCards(self._folds)

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

    def chooseContract(self, gui, contract: Contract.Contract) -> Contract:
        possibleContracts = []

        if (contract):
            possibleContracts = [-1]
            possibleContracts += [i for i in range(int(contract) + 1, 4)]
        else:
            possibleContracts = [i for i in range(-1, 4)]

        if (len(possibleContracts) == 0):
            return None

        strContracts = {}
        strContracts[-1] = QCoreApplication.translate("chooseContract", "Pass")

        for i in range(0, 4):
            strContracts[i] = str(Contract.Contract(i))

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
                return Contract.Contract(contract)
        else:
            guessContract = None

            oudlerCount = common.countOudlersForCards(self._cards)
            
            assets = []
            families = {Family.Family.Heart: [],
                        Family.Family.Club: [],
                        Family.Family.Diamond: [],
                        Family.Family.Spade: []}
            for card in self._cards:
                if card.isAsset():
                    assets.append(card)
                else: #elif card.isFamilyCard():
                    families[card.familyCard().family()].append(card)
            assets = sorted(assets, key = lambda x: x.value())
            for k, v in families.items():
                families[k] = sorted(families[k], key = lambda x: x.value())
            
            points = 0
            
            for card in self._cards:
                points += card.points()
            
            if (oudlerCount == 0):
                guessContract = None
            elif (oudlerCount == 1):
                if (len(assets) >= 22 // 3):
                    guessContract = Contract.Contract.Guard
                else:
                    guessContract = Contract.Contract.Little
            else:
                cutCount = 0
                
                for k, v in families.items():
                    if (len(families[k]) == 0):
                        cutCount += 1

                if (cutCount == 0):
                    guessContract = Contract.Contract.Guard
                else:
                    if (points >= common.maximumPoints() // self._game._playerNumber):
                        guessContract = Contract.Contract.GuardAgainst
                    else:
                        guessContract = Contract.Contract.GuardWithout
            
            if (not guessContract
                or (contract and guessContract.value <= contract.value)):
                return None
            
            return guessContract
    
    def callKing(self, gui) -> Family:
        strFamilies = {}
        choices = []
        
        for i in range(0, 4):
            strFamilies[i] = str(Family.Family(i))
            choices.append(str(Family.Family(i)))
        
        calledKing = None
        
        if (self._isHuman):
            gui._kingLabel.setVisible(True)
            gui._kingComboBox.setVisible(True)
            gui._ok = False
            
            while (not gui._ok):
                QtTest.QTest.qWait(10)
            
            calledKing = Family.Family({v: k for k, v in strFamilies.items()}.get(choices[gui._kingComboBox.currentIndex()]))
            
            gui._kingLabel.setVisible(False)
            gui._kingComboBox.setVisible(False)
        else:
            families = {Family.Family.Heart: [],
                        Family.Family.Club: [],
                        Family.Family.Diamond: [],
                        Family.Family.Spade: []}
            familyPoints = {Family.Family.Heart: 0,
                            Family.Family.Club: 0,
                            Family.Family.Diamond: 0,
                            Family.Family.Spade: 0}
            kings = {Family.Family.Heart: False,
                     Family.Family.Club: False,
                     Family.Family.Diamond: False,
                     Family.Family.Spade: False}
            for card in self._cards:
                if card.isFamilyCard():
                    families[card.familyCard().family()].append(card)
                    familyPoints[card.familyCard().family()] += card.points()
                    
                    if (card.value() == 14):
                        kings[card.familyCard().family()] = True
            for k, v in families.items():
                families[k] = sorted(families[k], key = lambda x: x.value())
            
            familyPoints = dict(sorted(familyPoints.items(), key = lambda item: item[1], reverse = True))
            kings = dict(sorted(kings.items(), key = lambda item: item[1]))
                
            for k, v in familyPoints.items():
                if (len(families[k]) and families[k][-1].value() != 14):
                    calledKing = k
                    break
            
            if (not calledKing):
                calledKing = list(kings.items())[0][0]

        return calledKing
    
    def doDog(self, gui, dog: list) -> list:
        newDog = []
        
        self._cards += dog
        self._cards = common.sortCards(self._cards)
        
        gui.displayTable([], False, True)

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
            cards = []
            
            for card in self._cards:
                if (not card.isAsset() and card.value() != 14):
                    cards.append(card)
            
            cards = sorted(cards, key = lambda x: x.value())

            newDog = cards[0:len(dog)]
            
            for c in newDog:
                del self._cards[self._cards.index(c)]
        
        assert(len(newDog) == len(dog))
        
        return common.sortCards(newDog)

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
  
        cardAssets = sorted(cardAssets, key = lambda x: x.value())
        
        handAssets = []
        handFamilies = {Family.Family.Heart: [],
                        Family.Family.Diamond: [],
                        Family.Family.Club: [],
                        Family.Family.Spade: []}
        
        for i in range(0, len(self._cards)):
            if (self._cards[i].isAsset()):
                handAssets.append(self._cards[i])
            else:
                handFamilies[self._cards[i].familyCard().family()].append(self._cards[i])
 
        handAssets = sorted(handAssets, key = lambda x: x.value())
        
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

                            if (add):
                                self._cuts[firstCard.familyCard().family()] = True
                        else:
                            if (self._cards[i].familyCard().family() != firstCard.familyCard().family()
                                and len(handAssets)):
                                add = False
                                self._cuts[self._cards[i].familyCard().family()] = True
            
            enabledCards.append(add)

        return enabledCards

    def playCard(self, gui, players: list, cards: dict, firstRound: bool, calledKing: Family.Family) -> Card.Card:
        QtTest.QTest.qWait(1000)

        card = None

        cardList = [x[1] for x in cards.items()]
        
        enabledCards = self.enabledCards(cardList, firstRound, calledKing)
        
        strCards = {}
        choices = []

        for i in range(0, len(enabledCards)):
            if (enabledCards[i]):
                strCards[i] = self._cards[i].name()
                choices.append(self._cards[i].name())

        gui.displayTable(cardList, True)

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
            assets = []
            families = {Family.Family.Heart: [],
                        Family.Family.Club: [],
                        Family.Family.Diamond: [],
                        Family.Family.Spade: []}
            for card in cardList:
                if card.isAsset():
                    assets.append(card)
                else: #elif card.isFamilyCard():
                    families[card.familyCard().family()].append(card)
            assets = sorted(assets, key = lambda x: x.value())
            for k, v in families.items():
                families[k] = sorted(families[k], key = lambda x: x.value())

            handAssets = []
            handFamilies = {Family.Family.Heart: [],
                            Family.Family.Club: [],
                            Family.Family.Diamond: [],
                            Family.Family.Spade: []}
            for card in self._cards:
                if card.isAsset():
                    handAssets.append(card)
                else: #elif card.isFamilyCard():
                    handFamilies[card.familyCard().family()].append(card)
            handAssets = sorted(handAssets, key = lambda x: x.value(), reverse = True)
            for k, v in handFamilies.items():
                handFamilies[k] = sorted(handFamilies[k], key = lambda x: x.value(), reverse = True)

            p, c = self._game.setWinner(cards)
        
            playedAssets, playedFamilies = self._game.playedCards()

            order = players.index(self._id)

            selectedCard = len(choices) - 1#selectedCard = random.randrange(len(choices))

            if (p == None):
                if (self._attackTeam):
                    if (self._game._taker == self._id):
                        if (len(handAssets) and len(handAssets) >= 22 // self._game._playerNumber):
                            assetIndex = len(handAssets) - 1
                            
                            if (handAssets[assetIndex].value() == 0):
                                assetIndex -= 1
                            if (handAssets[assetIndex].value() == 1):
                                assetIndex -= 1
                            
                            if (assetIndex < 0):
                                assetIndex = -1
                            
                            selectedCard = choices.index(handAssets[assetIndex].name())
                        else:
                            if (self._game._calledKing
                                and not playedFamilies[self._game._calledKing]
                                and len(handFamilies[self._game._calledKing])):
                                selectedCard = choices.index(handFamilies[self._game._calledKing][-1].name())
                            else:
                                for k, v in families.items():
                                    bestCard = 15
                                    
                                    if (len(playedFamilies[k])):
                                        bestCard = playedFamilies[k][-1].value()
                                        
                                    if (len(families[k]) and families[k][-1] >= bestCard - 1):
                                        cut = False
                                        
                                        for i in range(0, self._game._playerNumber):
                                            if (self._game._players[i]._cuts[families[k]]):
                                                cut = True
                                                break
                                        
                                        if (not cut):
                                            selectedCard = choices.index(handFamilies[k][-1].name())
                    else:
                        takerOrder = players.index(self._game._taker)
                        
                        if (order < takerOrder):
                            if (len(assets)):
                                index = 0
                                
                                if (assets[index].name() == "asset-1"):
                                    index -= 1
                                
                                selectedCard = choices.index(assets[index])
                            else:
                                familyIsPlayed = {Family.Family.Heart: False,
                                                  Family.Family.Club: False,
                                                  Family.Family.Diamond: False,
                                                  Family.Family.Spade: False}
                                playedFamily = False
                                    
                                for k, v in playedFamilies.items():
                                    if (len(v)):
                                        familyIsPlayed[k] = True
                                        playedFamily = True
                                
                                familyIsPlayed = dict(sorted(familyIsPlayed.items(), key = lambda item: item[1], reverse = True))
                            
                                if (playedFamily):
                                    i = 0
                                    
                                    while (i < 4):
                                        try:
                                            selectedCard = choices.index(handFamilies[familyIsPlayed[i]][0].name())
                                            i = 4
                                        except:
                                            pass
                                            
                                        i += 1
                                else:
                                    ok = False
                                    
                                    while (not ok):
                                        try:
                                            selectedCard = choices.index(handFamilies[Family(random.randrange(4))][0].name())
                                            ok = True
                                        except:
                                            pass
                        else:
                            familyIsPlayed = {Family.Family.Heart: False,
                                              Family.Family.Club: False,
                                              Family.Family.Diamond: False,
                                              Family.Family.Spade: False}
                                
                            for k, v in playedFamilies.items():
                                if (len(v)):
                                    familyIsPlayed[k] = True
                            
                            familyIsPlayed = dict(sorted(familyIsPlayed.items(), key = lambda item: item[1], reverse = True))
                            
                            try:
                                selectedCard = choices.index(handFamilies[playedFamilies[0]][0].name())
                            except:
                                pass
                else:
                    takerOrder = players.index(self._game._taker)
                        
                    if (order < takerOrder):
                        familyIsPlayed = {Family.Family.Heart: False,
                                          Family.Family.Club: False,
                                          Family.Family.Diamond: False,
                                          Family.Family.Spade: False}
                        emptyFamilies = {Family.Family.Heart: False,
                                         Family.Family.Club: False,
                                         Family.Family.Diamond: False,
                                         Family.Family.Spade: False}
                                         
                        for k, v in playedFamilies.items():
                            if (len(v)):
                                familyIsPlayed[k] = True
                        for k, v in handFamilies.items():
                            if (not len(v)):
                                emptyFamilies[k] = True
                        
                        playedFamilies = dict(sorted(familyIsPlayed.items(), key = lambda item: item[1]))
                        
                        if (list(emptyFamilies.values()).count(True) == 4):
                            index = 0
                                
                            if (handAssets[index].name() == "asset-1"):
                                index -= 1
                            
                            selectedCard = choices.index(handAssets[index].name())
                        else:
                            i = 0
                                        
                            while (i < 4):
                                try:
                                    selectedCard = choices.index(handFamilies[familyIsPlayed[i]][0].name())
                                    i = 4
                                except:
                                    pass
                                    
                                i += 1
                    else:
                        if (len(assets)):
                            selectedCard = choices.index(assets[0].name())
                        else:
                            playedFamily = None
                            
                            for k, v in playedFamilies.items():
                                if (len(v)):
                                    playedFamily = k
                                    break
                            
                            if (playedFamily):
                                selectedCard = choices.index(handFamilies[playedFamily][0].name())
                            else:
                                selectedCard = choices.index(handFamilies[Family(random.randrange(4))][0].name())
            else:
                if (self._game._players[p].teamKnown()):
                    if (c.isFamilyCard()):
                        bestCard = 15
                
                        if (len(playedFamilies[c.familyCard().family()])):
                            bestCard = playedFamilies[c.familyCard().family()][-1].value()
                    
                        if (self._game._players[p].attackTeam()):
                            if (self._attackTeam):
                                if (choices[0].startswith("asset-")):
                                    selectedCard = -1
                                else:    
                                    selectedCard = 0
                            else:
                                if (len(families[c.familyCard().family()])
                                    and families[c.familyCard().family()][-1].value() >= bestCard - 1):
                                    selectedCard = 0
                                else:
                                    selectedCard = -1
                        else:
                            if (not self._attackTeam):
                                if (choices[0].startswith("asset-")):
                                    selectedCard = -1
                                else:    
                                    selectedCard = 0
                            else:
                                selectedCard = -1
                    else: #elif (c.isAsset()):
                        bestAsset = 22
                        
                        if (len(playedAssets)):
                            bestAsset = playedAssets[-1].value()
                    
                        assetOneIndex = -1
                        
                        for i in range(0, len(self._cards)):
                            if (self._cards[i].isAsset() and self._cards[i].value() == 1):
                                assetOneInCards = i
                                break
                    
                        if (self._game._players[p].attackTeam()):
                            if (self._attackTeam):
                                if (assets[-1].value() >= bestAsset - 1
                                    and assetOneIndex != -1):
                                    selectedCard = choices.index(self._cards[assetOneIndex].name())
                            else:
                                if (choices[selectedCard] == "asset-1" and selectedCard - 1 >= 0):
                                    selectedCard -= 1
                        else:
                            if (not self._attackTeam):
                                if (assets[-1].value() >= bestAsset - 1
                                    and assetOneIndex != -1):
                                    selectedCard = choices.index(self._cards[assetOneIndex].name())
                            else:
                                if (choices[selectedCard] == "asset-1" and selectedCard - 1 >= 0):
                                    selectedCard -= 1
                else:
                    if (c.isFamilyCard()):
                        selectedCard = 0
                    else: #elif (c.isAsset()):
                        index = -1
                        
                        if (choices[index] == "asset-1"):
                            index -= 1
                        
                        try:
                            selectedCard = choices[index]
                            selectedCard = index
                        except:
                            pass

            if (selectedCard == -1 or selectedCard == len(choices) - 1):
                points = 10
                
                for card in reversed(self._cards):
                    if (card.name() in choices):
                        if (card.points() < points):
                            selectedCard = choices.index(card.name())
                            points = card.points()

            selectedCard = {v: k for k, v in strCards.items()}.get(choices[selectedCard])
            
            card = self._cards[selectedCard]
            del self._cards[selectedCard]
        
        return card
    
