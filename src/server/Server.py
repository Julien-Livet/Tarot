from common import Family
from common import common
from datetime import datetime
import random
import socket
import struct
import threading
import time

timeout = 30

class Room:
    def __init__(self, id: int, game):
        self._id = id
        self._clients = []
        self._game = game
        self._chosenContract = False
        self._started = False

class Server:
    def __init__(self, host = 'localhost', port = 12345):
        self._closed = True
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind((host, port))
        self._socket.listen(1)
        self._closed = False
        self._socket.settimeout(1)
        self._rooms  = {3: {}, 4: {}, 5: {}}
        self._clientRooms = {}
        self._gameRooms = {}
        self._roomCount = 0

    def __del__(self):
        self.disconnect()

    def disconnect(self):
        if (not self._closed):
            self._socket.close()

        self._closed = True

    def handleClient(self, clientSocket, clientAddress):
        from common import Game

        init = True

        roomId = -1

        data = b""
            
        while (init):
            if (self._closed):
                return

            try:
                data += clientSocket.recv(1024)
            except TimeoutError:
                pass
            print("server-data", data)
            if (data and data.startswith(b"room-")):
                playerNumber = struct.unpack('!i', data[len(b"room-"):len(b"room-") + 4])[0]
            
                found = False
                    
                for id, room in self._rooms[playerNumber].items():
                    if (len(room._clients) < playerNumber):
                        roomId = id
                        room._clients.append(clientSocket)
                        self._clientRooms[clientSocket] = (playerNumber, room._id)
                        found = True

                if (not found):
                    room = Room(self._roomCount, Game.Game(self, playerNumber))
                    room._game.giveHands()
                    room._clients.append(clientSocket)
                    self._rooms[playerNumber][self._roomCount] = room
                    self._clientRooms[clientSocket] = (playerNumber, self._roomCount)
                    self._gameRooms[room._game] = (playerNumber, self._roomCount)
                    roomId = self._roomCount
                    self._roomCount += 1
                
                init = False
                
                data = data[len(b"room-") + 4:]
                
        gameData = Game.GameData(3)
        for key, value in vars(room._game).items():
            if (key != "_server"):
                setattr(gameData, key, value)

        common.sendDataMessage(clientSocket, b"game-", gameData, self._closed)

        clientSocket.send(b"connect-" + struct.pack('!i', room._clients.index(clientSocket)))
        
        if (not room._started and len(room._clients) == playerNumber):
            room._started = True

            random.shuffle(room._clients)

            threading.Thread(target = room._game.play).start()
        
        room = self._rooms[playerNumber][roomId]

        while (room._game._gameState != Game.GameState.End):
            try:
                data += clientSocket.recv(1024)
            except TimeoutError:
                pass
                
            if (self._closed):
                return
            print("server-data", data)
            if (data):
                if (data.startswith(b"game-")):
                    ok, data, obj = common.receiveDataMessage(clientSocket, data, b"game-", self._closed)

                    room._game.__dict__.update(vars(obj))

                    for client in room._clients:
                        if (client != clientSocket):
                            common.sendDataMessage(client, b"game-", obj, self._closed)
                elif (data.startswith(b"disconnect")):
                    room._game._players[room._clients.index(clientSocket)]._connected = False
                    #TODO: ...
                    
                    data = data[len(b"disconnect"):]
                    
                    pass
                elif (data.startswith(b"chosenContract-")):
                    ok, data, obj = common.receiveDataMessage(clientSocket, data, b"chosenContract-", self._closed)

                    self._contract = obj
                    
                    room._chosenContract = True
                elif (data.startswith(b"calledKing-")):
                    ok, data, obj = common.receiveDataMessage(clientSocket, data, b"calledKing-", self._closed)

                    self._calledKing = obj

        del self._clientRooms[clientSocket]
        del self._rooms[playerNumber][roomId]
        del self._gameRooms[room._game]

    def acceptConnections(self):
        while (not self._closed):
            try:
                clientSocket, clientAddress = self._socket.accept()
                clientSocket.settimeout(1)

                threading.Thread(target = self.handleClient, args = (clientSocket, clientAddress)).start()
            except TimeoutError:
                pass
            except OSError:
                pass

    def chooseContract(self, game):
        self._contract = None
        currentTime = datetime.now()

        if (self._closed):
            return self._contract

        playerNumber, roomId = self._gameRooms[game]
        room = self._rooms[playerNumber][roomId]
        room._clients[game._currentPlayer].send(b"chooseContract")
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
        room._clients[game._currentPlayer].send(b"callKing")
        
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
        room._clients[game._currentPlayer].send(b"doDog")
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
        room._clients[game._currentPlayer].send(b"playCard")
        
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

if (__name__ == '__main__'):
    server = Server()
    server.acceptConnections()
