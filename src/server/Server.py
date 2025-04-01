from common import Family
from common import Game
from common import common
from datetime import datetime
import random
import rpyc
import time

timeout = 30

class Room:
    def __init__(self, id: int, game):
        self._id = id
        self._clients = []
        self._game = game
        self._chosenContract = False
        self._started = False

@rpyc.service
class Service(rpyc.Service):
    def __init__(self):
        super().__init__()
        self._clients = []
        self._rooms  = {3: {}, 4: {}, 5: {}}
        self._roomCount = 0
        self._gameRooms = {}

    def on_connect(self, conn):
        self._clients.append(conn)
        print(conn.root.hi())
        print("here")
        print(conn.root.setConn(conn))
        print("there")
        print(conn.root.hi())
        print("lol")

    def on_disconnect(self, conn):
        del self._clients[self._clients.index(conn)]

    @rpyc.exposed
    def hello(self):
        return "hello"

    @rpyc.exposed
    def join_room(self, playerNumber):
        assert(3 <= playerNumber and playerNumber <= 5)
    
        roomId = None
        found = False
    
        for id, room in self._rooms[playerNumber].items():
            if (len(room._clients) < playerNumber):
                roomId = id
                room._clients.append(clientSocket)
                found = True

        if (not found):
            room = Room(self._roomCount, Game.Game(self, playerNumber))
            room._game.giveHands()
            room._clients.append(conn)
            self._rooms[playerNumber][self._roomCount] = room
            self._gameRooms[room._game] = (playerNumber, self._roomCount)
            roomId = self._roomCount
            self._roomCount += 1
        
        return roomId
        
    @rpyc.exposed
    def gameData(self, roomId):    
        gameData = Game.GameData(3)
        for key, value in vars(self._rooms[roomId]._game).items():
            if (key != "_server"):
                setattr(gameData, key, value)

        return gameData

    def chooseContract(self, game):
        self._contract = None
        currentTime = datetime.now()

        if (self._closed):
            return self._contract

        playerNumber, roomId = self._gameRooms[game]
        room = self._rooms[playerNumber][roomId]

        for client in room._clients:
            common.sendDataMessage(client, b"currentPlayer-", room._game._currentPlayer, self._closed, "server")

        room._clients[game._currentPlayer].sendall(b"chooseContract")
        #print("server" + str(room._clients[game._currentPlayer].fileno()) + ">", b"chooseContract")
        room._chosenContract = False

        while (not self._closed
               and not room._chosenContract
               and (self._contract == None
                    or (datetime.now() - currentTime).total_seconds() <= timeout)):
            time.sleep(0.1)
            game._remainingTime = max(0, (datetime.now() - currentTime).total_seconds())

        return self._contract

    def callKing(self, game):
        self._calledKing = None
        currentTime = datetime.now()

        playerNumber, roomId = self._gameRooms[game]
        room = self._rooms[playerNumber][roomId]
        room._clients[game._currentPlayer].sendall(b"callKing")
        #print("server" + str(room._clients[game._currentPlayer].fileno()) + ">", b"callKing")

        while (not self._closed
               and (self._calledKing == None
                    or (datetime.now() - currentTime).total_seconds() <= timeout)):
            time.sleep(0.1)
            game._remainingTime = max(0, (datetime.now() - currentTime).total_seconds())

        if (self._calledKing == None):
            self._calledKing = Family.Family(random.randrange(4))

        return self._calledKing

    def doDog(self, game):
        self._dog = None
        currentTime = datetime.now()
        
        playerNumber, roomId = self._gameRooms[game]
        room = self._rooms[playerNumber][roomId]
        room._clients[game._currentPlayer].sendall(b"doDog")
        #"server" + str(room._clients[game._currentPlayer].fileno()) + ">", b"doDog")
        #TODO: ajouter des données pour faire le chien

        while (not self._closed
               and (self._dog == None
                    or (datetime.now() - currentTime).total_seconds() <= timeout)):
            time.sleep(0.1)
            game._remainingTime = max(0, (datetime.now() - currentTime).total_seconds())
            
        if (self._dog == None):
            player = room._game._players[room._game._currentPlayer]
            enabledCards = player.enabledCards(room._game._centerCards, room._game._firstRound, room._game._calledKing, True)
            
            cards = []
            
            for i in range(0, len(enabledCards)):
                if (enabledCards[i]):
                    cards.append(player._cards[i])
            
            self._dog = []

            while (len(self._dog) != len(room._game._dog)):
                i = random.randrange(len(player._cards))
                self._dog.append(player._cards[i])
                del player._cards[i]

        return self._dog

    def playCard(self, game):
        self._playedCard = None
        currentTime = datetime.now()

        playerNumber, roomId = self._gameRooms[game]
        room = self._rooms[playerNumber][roomId]
        room._clients[game._currentPlayer].sendall(b"playCard")
        #print("server" + str(room._clients[game._currentPlayer].fileno()) + ">", b"playCard")

        while (not self._closed
               and (self._playedCard == None
                    or (datetime.now() - currentTime).total_seconds() <= timeout)):
            time.sleep(0.1)
            game._remainingTime = max(0, (datetime.now() - currentTime).total_seconds())

        if (self._playedCard == None):
            player = room._game._players[room._game._currentPlayer]
            enabledCards = player.enabledCards(room._game._centerCards, room._game._firstRound, room._game._calledKing, False)
            
            cards = []
            
            for i in range(0, len(enabledCards)):
                if (enabledCards[i]):
                    cards.append(player._cards[i])
            
            self._playedCard = cards[random.randrange(len(cards))]

        return self._playedCard

def runServer(port):
    from rpyc.utils.server import ThreadedServer
    server = ThreadedServer(GameService, port = port)
    server.start()

if (__name__ == '__main__'):
    runServer(18861)
