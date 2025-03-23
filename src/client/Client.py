from common import Game
import pickle
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
        while (not self._closed):
            data = None
            
            try:
                data = self._socket.recv(1024)
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

                    self._gameData = pickle.loads(data)
                elif (data.startswith(b"connect-")):
                    self._id = int(data.split(b"connect-")[1])

                    self._gameData._players[self._id]._name = self._gui._lineEdit.text()
                    self._gameData._players[self._id]._avatar = self._gui._avatar
                    self._gameData._players[self._id]._isHuman = self._isHuman

                    send = True
                    
                    while (send):     
                        try:
                            data = pickle.dumps(self._gameData)
                            self._socket.send(b"game-" + struct.pack('!i', len(data)))
                            self._socket.send(data)
                            send = False
                        except:
                            pass
                elif (data == b"play"):
                    pass
