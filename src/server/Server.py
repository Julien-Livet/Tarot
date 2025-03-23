from common import Family
from datetime import datetime
import pickle
from PyQt5.QtCore import QTimer
import random
import socket
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
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind((host, port))
        self._socket.listen(1)
        self._rooms  = {3: {}, 4: {}, 5: {}}
        self._clientRooms = {}
        self.gameRooms = {}
        self._roomCount = 0

    def __del__(self):
        self._socket.close()
        
    def handleClient(self, clientSocket, clientAddress):
        init = True
        
        while (init):
            data = clientSocket.recv(1024).decode()

            if (data and data.startswith("room-")):
                playerNumber = int(data.split("room-")[1])
            
                found = False
                    
                for room in rooms[playerNumber]:
                    if (len(room.players) < playerNumber):
                        room._clients.append(clientSocket)
                        self._clientRooms[clientSocket] = (playerNumber, room.id)
                        found = True

                        if (len(room._clients == playerNumber)):
                            room._clients = random.shuffle(room._clients)

                            room._game.giveHands()
                            threading.Thread(target = room._game.play).start()

                if (not found):
                    room = Room(self._roomCount, Game(self, playerNumber))
                    self._rooms[playerNumber][self._roomCount] = room
                    self._clientRooms[clientSocket] = (playerNumber, self._roomCount)
                    self._gameRooms[room._game] = (playerNumber, self._roomCount)
                    self._roomCount += 1
                
                init = False
                
                gameData = Game.GameData(**{key: value for key, value in vars(self._game).items() if key != "_server"})
                clientSocket.send(("game-" + pickle.dumps(gameData)).encode())
                clientSocket.send(("connect-" + str(room._clients.index(clientSocket))).encode())
        
        room = self._rooms[playerNumber][roomId]
        
        while (room._game._gameState != Game.GameState.End):
            data = clientSocket.recv(1024).decode()

            if (data):
                if (data.startswith("game-")):
                    gameData = int(data.split("game-")[1])
                    
                    playerNumber, roomId = self._clientRooms[clientSocket]
                    room = self._rooms[playerNumber][roomId]

                    room._game.__dict__.update(vars(pickle.loads(gameData)))
                    
                    for client in room._clients:
                        if (client != clientSocket):
                            client.send(data.encode())
                elif (data == "disconnect"):
                    #TODO: ...
                    
                    pass

    def acceptConnections(self):
        while (True):
            clientSocket, clientAddress = self._socket.accept()
            
            threading.Thread(target = self.handleClient, args = (clientSocket, clientAddress)).start()
        
    def chooseContract(self, game):
        self._contract = None
        currentTime = datetime.now()

        while (self._contract == None
               or (datetime.now() - currentTime).total_seconds() <= timeout):
            time.sleep(0.01)
            game._remainingTime = max(0, (datetime.now() - currentTime).total_seconds())

        return self._contract

    def callKing(self, game):
        self._calledKing = None
        currentTime = datetime.now()
    
        while (self._calledKing == None
               or (datetime.now() - currentTime).total_seconds() <= timeout):
            time.sleep(0.01)
            game._remainingTime = max(0, (datetime.now() - currentTime).total_seconds())
            
        if (self._calledKing == None):
            self._calledKing = Family.Family(random.randrange(4))
            
        return self._dog

    def doDog(self, game):
        self._dog = None
        currentTime = datetime.now()
    
        while (self._dog == None
               or (datetime.now() - currentTime).total_seconds() <= timeout):
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
    
        while (self._playedCard == None
               or (datetime.now() - currentTime).total_seconds() <= timeout):
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
