from common import Family
from datetime import datetime
import pickle
from PyQt5.QtCore import QTimer
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
            
        while (init):
            data = None
            
            try:
                data = clientSocket.recv(1024)
            except:
                pass
                
            if (self._closed):
                return

            if (data and data.startswith(b"room-")):
                playerNumber = int(data.split(b"room-")[1])
            
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
                
        gameData = Game.GameData(3)
        for key, value in vars(room._game).items():
            if (key != "_server"):
                setattr(gameData, key, value)

        send = True
        
        while (send):     
            try:
                data = pickle.dumps(gameData)
                clientSocket.send(b"game-" + struct.pack('!i', len(data)))
                clientSocket.send(data)
                send = False
            except:
                pass
        
        clientSocket.send(("connect-" + str(room._clients.index(clientSocket))).encode())
        
        if (len(room._clients) == playerNumber):
            random.shuffle(room._clients)

            threading.Thread(target = room._game.play).start()
        
        room = self._rooms[playerNumber][roomId]

        while (room._game._gameState != Game.GameState.End):
            data = None
            
            try:
                data = clientSocket.recv(1024)
            except:
                pass
                
            if (self._closed):
                return

            if (data):
                if (data.startswith(b"game-")):
                    size = struct.unpack('!i', data[len(b"game-"):len(b"game-") + 4])[0]

                    data = data[len(b"game-") + 4:]
                    
                    while (len(data) < size):
                        try:
                            data += self._socket.recv(1024)
                        except:
                            pass

                    room._game.__dict__.update(vars(pickle.loads(data)))
                    
                    for client in room._clients:
                        if (client != clientSocket):
                            client.send(b"game-" + struct.pack('!i', size))
                            client.send(data)
                elif (data == b"disconnect"):
                    room._game._players[room._clients.index(clientSocket)]._connected = False
                    #TODO: ...
                    
                    pass
        
        del self._clientRooms[clientSocket]
        del self._rooms[playerNumber][roomId]
        del self._gameRooms[room._game]

    def acceptConnections(self):
        while (not self._closed):
            try:
                clientSocket, clientAddress = self._socket.accept()
                clientSocket.settimeout(1)

                threading.Thread(target = self.handleClient, args = (clientSocket, clientAddress)).start()
            except:
                pass
        
    def chooseContract(self, game):
        self._contract = None
        currentTime = datetime.now()

        while (not self._closed
               and (self._contract == None
                    or (datetime.now() - currentTime).total_seconds() <= timeout)):
            time.sleep(0.01)
            game._remainingTime = max(0, (datetime.now() - currentTime).total_seconds())

        return self._contract

    def callKing(self, game):
        self._calledKing = None
        currentTime = datetime.now()

        while (not self._closed
               and (self._calledKing == None
                    or (datetime.now() - currentTime).total_seconds() <= timeout)):
            time.sleep(0.01)
            game._remainingTime = max(0, (datetime.now() - currentTime).total_seconds())

        if (self._calledKing == None):
            self._calledKing = Family.Family(random.randrange(4))

        return self._dog

    def doDog(self, game):
        self._dog = None
        currentTime = datetime.now()

        while (not self._closed
               and (self._dog == None
                    or (datetime.now() - currentTime).total_seconds() <= timeout)):
            time.sleep(0.01)
            game._remainingTime = max(0, (datetime.now() - currentTime).total_seconds())
            
        if (self._dog == None):
            player = self._game._players[self._game._currentPlayer]
            enabledCards = player.enabledCards(self._game._centerCards, self._game._firstRound, self._game._calledKing, True)
            
            cards = []
            
            for i in range(0, len(enabledCards)):
                if (enabledCards[i]):
                    cards.append(player._cards[i])
            
            self._dog = []
            
            while (len(self._dog) != len(self._game._dog)):
                i = random.randrange(len(player._cards))
                self._dog.append(player._cards[i])
                del player._cards[i]

        return self._dog

    def playCard(self, game):
        self._playedCard = None
        currentTime = datetime.now()

        while (not self._closed
               and (self._playedCard == None
                    or (datetime.now() - currentTime).total_seconds() <= timeout)):
            time.sleep(0.01)
            game._remainingTime = max(0, (datetime.now() - currentTime).total_seconds())
            
        if (self._playedCard == None):
            player = self._game._players[self._game._currentPlayer]
            enabledCards = player.enabledCards(self._game._centerCards, self._game._firstRound, self._game._calledKing, False)
            
            cards = []
            
            for i in range(0, len(enabledCards)):
                if (enabledCards[i]):
                    cards.append(player._cards[i])
            
            self._playedCard = cards[random.randrange(len(cards))]

        return self._playedCard

if (__name__ == '__main__'):
    server = Server()
    server.acceptConnections()
