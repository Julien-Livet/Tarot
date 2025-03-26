from common import Game
from common import common
import socket
import struct
import threading

class Client:
    def __init__(self, gui, playerNumber, isHuman = True, host = 'localhost', port = 12345):
        assert(3 <= playerNumber and playerNumber <= 5)

        self._gui = gui
        self._closed = True
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((host, port))
        self._closed = False
        self._socket.settimeout(5)
        self._gameData = None
        self._playerNumber = playerNumber
        self._id = None
        self._isHuman = isHuman
        
        threading.Thread(target = self.receiveData).start()

    def __del__(self):
        self.disconnect()
 
    def disconnect(self):
        if (not self._closed):
            self._socket.send(b"disconnect")
        
        self._closed = True
        
        if (not self._closed):
            self._socket.close()
        
    def receiveData(self):
        data = b""

        while (not self._closed):
            try:
                data += self._socket.recv(1024)
            except TimeoutError:
                pass
            print("client-data", data)
            if (data):
                if (data.startswith(b"game-")):
                    ok, data, obj = common.receiveDataMessage(self._socket, data, b"game-", self._closed)

                    self._gameData = obj

                    if (self._id):
                        self._gameData._players[self._id]._name = self._gui._lineEdit.text()
                        self._gameData._players[self._id]._avatar = self._gui._avatar
                        self._gameData._players[self._id]._isHuman = self._isHuman
                elif (data.startswith(b"connect-")):
                    self._id = size = struct.unpack('!i', data[len(b"connect-"):len(b"connect-") + 4])[0]

                    self._gameData._players[self._id]._name = self._gui._lineEdit.text()
                    self._gameData._players[self._id]._avatar = self._gui._avatar
                    self._gameData._players[self._id]._isHuman = self._isHuman

                    common.sendDataMessage(self._socket, b"game-", self._gameData, self._closed)

                    data = data[len(b"connect-") + 4:]
                elif (data.startswith(b"chooseContract")):
                    contract = self._gameData._players[self._id].chooseContract(self._gui, self._gameData._contract)

                    common.sendDataMessage(self._socket, b"chosenContract-", contract, self._closed)

                    data = data[len(b"chooseContract"):]
                elif (data.startswith(b"callKing")):
                    calledKing = self._gameData._players[self._id].callKing(self._gui)

                    common.sendDataMessage(self._socket, b"calledKing-", calledKing, self._closed)

                    data = data[len(b"callKing"):]
                elif (data.startswith(b"doDog")):
                    #TODO: ...

                    data = data[len(b"doDog"):]
                elif (data.startswith(b"play")):
                    #TODO: ...

                    data = data[len(b"play"):]
