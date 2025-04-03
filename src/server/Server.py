from common import Family
from common import Game
from common import common
from datetime import datetime
import pickle
import random
import rpyc
import time
import threading

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
    _clients = []
    _rooms  = {3: {}, 4: {}, 5: {}}
    _roomCount = 0
    _gameRooms = {}
    _clientRooms = {}
    
    def __init__(self):
        super().__init__()
        self._conn = None
        self._playerNumber = None
        self._roomId = None

    def on_connect(self, conn):
        conn._config["allow_pickle"] = True
        Service._clients.append(conn)
        self._conn = conn

    def on_disconnect(self, conn):
        del Service._clients[Service._clients.index(self._conn)]
        del Service._clientRooms[self._conn]

    @rpyc.exposed
    def null(self):
        pass
    
    @rpyc.exposed
    def remainingTime(self):
        return Service._clientRooms[self._conn]._game._remainingTime
    
    @rpyc.exposed
    def currentPlayer(self):
        return Service._clientRooms[self._conn]._game._currentPlayer
    
    @rpyc.exposed
    def connect(self, data):
        room = Service._clientRooms[self._conn]
        i = room._clients.index(self._conn)
        
        info = pickle.loads(data)
        
        room._game._players[i]._isHuman = info[0]
        room._game._players[i]._name = info[1]
        room._game._players[i]._avatar = info[2]
    
    @rpyc.exposed
    def join_room(self, playerNumber):
        assert(3 <= playerNumber and playerNumber <= 5)
        
        self._playerNumber = playerNumber

        roomId = None
        found = False

        for id, room in Service._rooms[playerNumber].items():
            if (len(room._clients) < playerNumber):
                roomId = id
                room._clients.append(self._conn)
                Service._clientRooms[self._conn] = room
                found = True

        if (not found):
            room = Room(Service._roomCount, Game.Game(self, playerNumber))
            room._game.giveHands()
            room._clients.append(self._conn)
            Service._rooms[playerNumber][Service._roomCount] = room
            Service._gameRooms[room._game] = (playerNumber, Service._roomCount)
            Service._clientRooms[self._conn] = room
            roomId = Service._roomCount
            Service._roomCount += 1
            
        self._roomId = roomId

        if (not room._started and len(room._clients) == playerNumber):
            room._started = True
 
            random.shuffle(room._clients)

            for i in range(0, len(room._clients)):
                room._clients[i].root.setId(i)

            threading.Thread(target = room._game.play).start()

        return roomId

    @rpyc.exposed
    def gameData(self):
        gameData = Game.GameData(3)
        for key, value in vars(Service._rooms[self._playerNumber][self._roomId]._game).items():
            if (key != "_server"):
                setattr(gameData, key, value)

        return pickle.dumps(gameData)

    def chooseContract(self, game):
        playerNumber, roomId = Service._gameRooms[game]
        room = Service._rooms[playerNumber][roomId]

        #TODO: Lancer un timer
        return room._clients[game._currentPlayer].root.chooseContract()

    def callKing(self, game):
        playerNumber, roomId = Service._gameRooms[game]
        room = Service._rooms[playerNumber][roomId]

        #TODO: Lancer un timer
        return room._clients[game._currentPlayer].root.callKing()

    def doDog(self, game):
        playerNumber, roomId = Service._gameRooms[game]
        room = Service._rooms[playerNumber][roomId]

        #TODO: Lancer un timer
        data = room._clients[room._game._taker].root.doDog(pickle.dumps(room._game._dog))
        player, dog = pickle.loads(data)
        room._game._players[game._taker] = player
        
        return dog

    def playCard(self, game, players, cards):        
        playerNumber, roomId = Service._gameRooms[game]
        room = Service._rooms[playerNumber][roomId]

        #TODO: Lancer un timer
        data = room._clients[room._game._currentPlayer].root.playCard(pickle.dumps((players, cards)))
        player, card = pickle.loads(data)
        room._game._players[game._currentPlayer] = player

        return card

def runServer(port):
    from rpyc.utils.server import ThreadedServer
    server = ThreadedServer(GameService, port = port)
    server.start()

if (__name__ == '__main__'):
    runServer(18861)

