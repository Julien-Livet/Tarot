from common import Game
from common import common
import rpyc

@rpyc.service
class Service(rpyc.Service):
    def __init__(self, client):
        self._client = client

    def on_connect(self, conn):
        pass
        
    def on_disconnect(self, conn):
        pass

    @rpyc.exposed
    def chooseContract(self):
        return self._client._gameData._players[self._id].chooseContract(self._gui, self._gameData._contract)

    @rpyc.exposed
    def callKing(self):
        return self._client._gameData._players[self._id].callKing(self._gui)

    @rpyc.exposed
    def hi(self):
        return "hi"

    @rpyc.exposed
    def setConn(self, conn):
        self._conn = conn
        
        return "setConn"

class Client:
    def __init__(self, gui, playerNumber, isHuman = True, host = 'localhost', port = 12345):
        assert(3 <= playerNumber and playerNumber <= 5)

        self._gui = gui
        self._conn = rpyc.connect(host, port, service = Service(self))
        print(self._conn.root.hello())
        self._playerNumber = playerNumber
        self._id = None
        self._isHuman = isHuman
        self._roomId = None #self._conn.root.join_room(self._playerNumber)
        self._gameData = None #self._conn.root.gameData(self._roomId)

    def close(self):
        if (self._conn and not self._conn.closed):
            self._conn.close()
