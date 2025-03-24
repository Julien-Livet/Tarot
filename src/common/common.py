from common import Asset
from common import Card
from common import Family
from common import FamilyCard
from common import Head
import os
import pickle
from PIL import Image
import struct
import sys

def maximumPoints():
    cards = []

    for i in range(0, 4):
        for j in range(1, 11):
            cards.append(Card.Card(familyCard = FamilyCard.FamilyCard(family = Family.Family(i), value = j)))
        for j in range(0, 4):
            cards.append(Card.Card(familyCard = FamilyCard.FamilyCard(family = Family.Family(i), head = Head.Head(j))))
    for i in range(0, 22):
        cards.append(Card.Card(asset = Asset.Asset(i)))
        
    points = 0
    
    for card in cards:
        points += card.points()
        
    return points

def playerRadius(playerNumber: int, globalRatio: float) -> float:
    assert(3 <= playerNumber and playerNumber <= 5)
    
    if (playerNumber == 3):
        return 225 * globalRatio
    elif (playerNumber == 4):
        return 260 * globalRatio
    elif (playerNumber == 5):
        return 290 * globalRatio

def countOudlersForCards(cards: list) -> int:
    count = 0

    for card in cards:
        if (card.isOudler()):
            count += 1

    return count

def imageForCards(cards: list, enabledCards: list, cardSize: tuple, overCardRatio :float, shown: bool = True):
    assert(len(cards) == len(enabledCards))

    if (len(cards) == 0):
        return None
    
    firstImage = None
    
    if (shown):
        firstImage = cards[0].image(cardSize)
    else:
        firstImage = Image.open(os.path.dirname(__file__) + "/../../images/back.png")
        
        firstImage = firstImage.resize(cardSize)

    image = Image.new('RGBA', (firstImage.width + int((len(cards) - 1) * firstImage.width * overCardRatio), firstImage.height))
    
    for i in range(0, len(cards)):
        im = None
        
        if (shown):
            im = cards[i].image(cardSize)
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
    families = {Family.Family.Heart: [],
                Family.Family.Club: [],
                Family.Family.Diamond: [],
                Family.Family.Spade: []}
    for card in cards:
        if card.isAsset():
            assets.append(card)
        else: #elif card.isFamilyCard():
            families[card.familyCard().family()].append(card)
    assets = sorted(assets, key = lambda x: x.value(), reverse = True)
    for k, v in families.items():
        families[k] = sorted(families[k], key = lambda x: x.value(), reverse = True)
    cards = assets
    if (len(families[Family.Family.Club]) == 0):
        families[Family.Family.Club], families[Family.Family.Spade] = families[Family.Family.Spade], families[Family.Family.Club]
    if (len(families[Family.Family.Diamond]) == 0):
        families[Family.Family.Diamond], families[Family.Family.Heart] = families[Family.Family.Heart], families[Family.Family.Diamond]
    families = [x[1] for x in families.items()]
    for f in families:
        cards += f
        
    return cards

def sendDataMessage(socket, message, obj, closed):
    send = True
                    
    while (send):     
        if (closed):
            return
            
        try:
            d = pickle.dumps(obj)
            socket.send(message + struct.pack('!i', len(d)))
            socket.send(d)
            send = False
        except TimeoutError:
            pass

def receiveDataMessage(socket, data, message, closed):
    if (not data.startswith(message)):
        return (False, data, None)

    size = struct.unpack('!i', data[len(message):len(message) + 4])[0]

    data = data[len(message) + 4:]
    
    while (len(data) < size):
        if (closed):
            return
    
        try:
            data += socket.recv(1024)
        except TimeoutError:
            pass

    obj = pickle.loads(data[:size])

    data = data[size:]

    return (True, data, obj)    
