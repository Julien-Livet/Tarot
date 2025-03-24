from common import Game
import pickle
import socket
import struct
import threading

class Client:
    def __init__(self, gui, playerNumber, isHuman = True, host = 'localhost', port = 1234):
        assert(3 <= playerNumber and playerNumber <= 5)

        self._gui = gui
        self._closed = True
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((host, port))
        self._closed = False
        self._socket.settimeout(1)
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
            except:
                pass

            if (data):
                if (data.startswith(b"game-")):
                    size = struct.unpack('!i', data[len(b"game-"):len(b"game-") + 4])[0]
                    
                    data = data[len(b"game-") + 4:]

                    while (len(data) < size):
                        try:
                            data += self._socket.recv(1024)
                        except:
                            pass

                    self._gameData = pickle.loads(data[:size])

                    if (self._id):
                        self._gameData._players[self._id]._name = self._gui._lineEdit.text()
                        self._gameData._players[self._id]._avatar = self._gui._avatar
                        self._gameData._players[self._id]._isHuman = self._isHuman

                    data = data[size:]
                elif (data.startswith(b"connect-")):
                    self._id = size = struct.unpack('!i', data[len(b"connect-"):len(b"connect-") + 4])[0]

                    self._gameData._players[self._id]._name = self._gui._lineEdit.text()
                    self._gameData._players[self._id]._avatar = self._gui._avatar
                    self._gameData._players[self._id]._isHuman = self._isHuman

                    send = True
                    
                    while (send):     
                        try:
                            d = pickle.dumps(self._gameData)
                            self._socket.send(b"game-" + struct.pack('!i', len(d)))
                            self._socket.send(d)
                            send = False
                        except:
                            pass
                    
                    data = data[len(b"connect-") + 4:]
                elif (data == b"chooseContract"):
                    contract = self._gameData._players[self._id].chooseContract(self._gui, self._gameData._contract)

                    send = True
                    
                    while (send):     
                        try:
                            d = pickle.dumps(contract)
                            self._socket.send(b"chosenContract-" + struct.pack('!i', len(d)))
                            self._socket.send(d)
                            send = False
                        except:
                            pass

                    data = data[len(b"chooseContract"):]
                elif (data == b"play"):
                    pass
