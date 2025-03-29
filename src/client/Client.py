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
        #self._socket.settimeout(1)
        self._gameData = None
        self._playerNumber = playerNumber
        self._id = None
        self._isHuman = isHuman
        
        threading.Thread(target = self.receiveData).start()

    def __del__(self):
        self.disconnect()
 
    def disconnect(self):
        if (not self._closed):
            self._socket.sendall(b"disconnect")
        
        self._closed = True
        
        if (not self._closed):
            self._socket.close()
        
    def receiveData(self):
        data = b""

        messages = []

        while (not self._closed):
            try:
                data += self._socket.recv(1024)
            except TimeoutError:
                pass
            
            while (data):
                found = False
                #print("client" + str(self._socket.fileno()) + "<", data)          
                if (data.startswith(b"gameData-")):
                    found = True
                    ok, data, obj = common.receiveDataMessage(self._socket, data, b"gameData-", self._closed, "client")
                    messages.append(("gameData-", obj))
                elif (data.startswith(b"player-")):
                    found = True
                    ok, data, obj = common.receiveDataMessage(self._socket, data, b"player-", self._closed, "client")
                    messages.append(("player-", obj))
                elif (data.startswith(b"currentPlayer-")):
                    found = True
                    ok, data, obj = common.receiveDataMessage(self._socket, data, b"currentPlayer-", self._closed, "client")
                    messages.append(("currentPlayer-", obj))
                elif (data.startswith(b"connect-")):
                    found = True
                    id = struct.unpack('!i', data[len(b"connect-"):len(b"connect-") + 4])[0]
                    messages.append(("connect-", id))
                    data = data[len(b"connect-") + 4:]
                elif (data.startswith(b"chooseContract")):
                    found = True
                    messages.append(("chooseContract", None))
                    data = data[len(b"chooseContract"):]
                elif (data.startswith(b"callKing")):
                    found = True
                    messages.append(("callKing", None))
                    data = data[len(b"callKing"):]
                elif (data.startswith(b"doDog")):
                    #TODO: ...

                    data = data[len(b"doDog"):]
                elif (data.startswith(b"play")):
                    #TODO: ...

                    data = data[len(b"play"):]
                    
                if (not found):
                    break

            newMessages = []

            for m in messages:
                process = True

                if (m[0] == "gameData-"):
                    print("client" + str(self._socket.fileno()), "gameData-")
                    self._gameData = m[1]
                elif (m[0] == "connect-"):
                    if (not self._gameData):
                        process = False
                    else:
                        print("client" + str(self._socket.fileno()), "connect-")
                        self._id = m[1]

                        self._gameData._players[self._id]._name = self._gui._lineEdit.text()
                        self._gameData._players[self._id]._avatar = self._gui._avatar
                        self._gameData._players[self._id]._isHuman = self._isHuman

                        common.sendDataMessage(self._socket, b"player-", (self._id, self._gameData._players[self._id]), self._closed, "client")
                elif (m[0] == "player-"):
                    if (not self._gameData):
                        process = False
                    else:
                        print("client" + str(self._socket.fileno()), "player-")
                        id, player = m[1]
                        self._gameData._players[id] = player
                elif (m[0] == "chooseContract"):
                    if (not self._id or not self._gameData):
                        process = False
                    else:
                        contract = self._gameData._players[self._id].chooseContract(self._gui, self._gameData._contract)

                        common.sendDataMessage(self._socket, b"chosenContract-", contract, self._closed, "client")
                elif (m[0] == "callKing"):
                    if (not self._id or not self._gameData):
                        process = False
                    else:
                        calledKing = self._gameData._players[self._id].callKing(self._gui)

                        common.sendDataMessage(self._socket, b"calledKing-", calledKing, self._closed, "client")
                elif (m[0] == "currentPlayer-"):
                    if (not self._gameData):
                        process = False
                    else:
                        print("client" + str(self._socket.fileno()), "currentPlayer-")
                        self._gameData._currentPlayer = m[1]

                if (not process):
                    newMessages.append(m)

            messages = newMessages
