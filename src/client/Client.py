from common import Game
from common import common
import pickle
import rpyc
import threading

@rpyc.service
class Service(rpyc.Service):
    def __init__(self, client):
        super().__init__()
        self._client = client

    def on_connect(self, conn):
        conn._config["allow_pickle"] = True
        
    def on_disconnect(self, conn):
        pass

    def getGameData(self):
        data = self._client._conn.root.gameData()
        
        self._client._gameData = pickle.loads(data)
        
        return self._client._gameData

    @rpyc.exposed
    def chooseContract(self):
        self.getGameData()

        return self._client._gameData._players[self._client._gameData._currentPlayer].chooseContract(self._client._gui, self._client._gameData._contract)

    @rpyc.exposed
    def callKing(self):
        self.getGameData()

        return self._client._gameData._players[self._client._gameData._taker].callKing(self._client._gui)

    @rpyc.exposed
    def doDog(self, data):
        dog = pickle.loads(data)
    
        self.getGameData()

        dog = self._client._gameData._players[self._client._gameData._taker].doDog(self._client._gui, dog)

        return pickle.dumps((self._client._gameData._players[self._client._gameData._taker], dog))

    @rpyc.exposed
    def playCard(self, data):
        self.getGameData()

        players, cards = pickle.loads(data)
        card = self._client._gameData._players[self._client._gameData._currentPlayer].playCard(self._client._gui, players, cards, self._client._gameData)

        return pickle.dumps((self._client._gameData._players[self._client._gameData._currentPlayer], card))

    @rpyc.exposed
    def setId(self, id):
        self.getGameData()
        
        self._client._id = id

        name = self._client._gameData._players[self._client._id]._name
        avatar = self._client._gameData._players[self._client._id]._avatar

        if (self._client._isHuman):
            name = self._client._gui._lineEdit.text()
            avatar = self._client._gui._avatar

        info = (self._client._isHuman, name, avatar)

        self._client._conn.root.connect(pickle.dumps(info))
        
        self.getGameData()

class Client:
    def __init__(self, gui, playerNumber, isHuman = True, host = 'localhost', port = 12345):
        assert(3 <= playerNumber and playerNumber <= 5)

        self._gui = gui
        self._conn = rpyc.connect(host, port, service = Service(self))
        self._playerNumber = playerNumber
        self._id = None
        self._isHuman = isHuman
        self._roomId = self._conn.root.join_room(self._playerNumber)
        self._gameData = None

        threading.Thread(target = self.update).start()

    def close(self):
        if (self._conn and not self._conn.closed):
            self._conn.close()

    def update(self):
        import time
    
        while (not self._conn.closed):
            time.sleep(0.1)
        
            try:
                data = self._conn.root.gameData()
                self._gameData = pickle.loads(data)
                self._gui._remainingTime = self._gameData._remainingTime
            except EOFError:
                pass
            except TimeoutError:
                pass
            except OSError:
                pass
                
            if (self._gameData._gameState == Game.GameState.End):
                self._conn.close()
