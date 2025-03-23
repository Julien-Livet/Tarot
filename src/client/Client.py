from common import Game
import socket

class Client:
    def __init__(self, gui, playerNumber, host = 'localhost'):
        assert(3 <= playerNumber and playerNumber <= 5)

        self._gui = gui
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((host, port))
        self._gameData = None
        self._playerNumber = playerNumber
        self._isClosed = False
        self._id = None
        
        threading.Thread(target = self.receiveData).start()

    def disconnect(self):
        self._socket.send("close".encode())
        self._isClosed = True
        self._socket.close()
        
    def receiveData(self):
        while (not self._isClosed):
            data = self._socket.recv(1024).decode()
        
            if (data.startswith("game-")):
                gameData = int(data.split("game-")[1])
                        
                room._gameData = pickle.loads(gameData)
            elif (data.startswith("connect-")):
                self._id = int(data.split("connect-")[1])
            elif (data == "play"):
                pass
