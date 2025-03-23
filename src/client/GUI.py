from common import Family
from common import TableLabel
from common import common
from client import Client
import io
import math
import os
from PyQt5.QtCore import QCoreApplication, QObject, Qt, QRectF, QTimer
from PyQt5.QtGui import QKeySequence, QPixmap, QPolygonF, QTransform
from PyQt5.QtWidgets import QApplication, QComboBox, QDialog, QHBoxLayout, QLineEdit, QMessageBox, QVBoxLayout, QLabel, QPushButton, QShortcut
import threading

iniFilename = os.path.dirname(__file__) + "/../../Tarot.ini"

class Window(QDialog):
    def __init__(self, gui):
        super().__init__()
        self._gui = gui
        
    def closeEvent(self, event):
        if (self._client)
            self._gui._client.disconnect()
        
        with open(iniFilename, 'w') as file:
            file.write(self._gui._lineEdit.text())

class GUI(QObject):
    def __init__(self):
        super().__init__()
        self._playerNumber = 5
        self._window = None
        self._dialog = None
        self._ok = False
        self._globalRatio = 0.8
        self._cardSize = (0, 0)
        self._overCardRatio = 1 / 3
        self._client = None

        assert(0 < self._overCardRatio and self._overCardRatio <= 1)

    def threePlayers(self):
        self._playerNumber = 3
        
        if (len(self._lineEdit.text())):
            self._dialog.accept()

    def fourPlayers(self):
        self._playerNumber = 4
        
        if (len(self._lineEdit.text())):
            self._dialog.accept()

    def fivePlayers(self):
        self._playerNumber = 5
        
        if (len(self._lineEdit.text())):
            self._dialog.accept()

    def displayTable(self, centerCards: list, displayCenterCards: bool = False, centerCardsIsDog: bool = False):
        img = self._gameData.tableImage(self, self._showPlayers, centerCards, displayCenterCards, centerCardsIsDog, self._client._id)

        byteArray = io.BytesIO()
        img.save(byteArray, format = 'PNG')
        pixmap = QPixmap()
        pixmap.loadFromData(byteArray.getvalue())
        self._tableLabel.setPixmap(pixmap)

    def comboBoxActivated(self, index: int):
        for i in range(0, 6):
            if (self._dogComboBoxes[i] == self.sender()):
                self._dogIndex = i
                break

    def play(self) -> bool:
        self._dialog = Window(self)
        self._dialog.setWindowTitle(QCoreApplication.translate("play", "Choose a game"))

        layout = QVBoxLayout()

        self._lineEdit = QLineEdit(self._dialog)
        self._lineEdit.setMaxLength(8)
        
        if (os.path.exists(iniFilename)):
            self._lineEdit.setText(file.read())
        
        threeButton = QPushButton(QCoreApplication.translate("play", "Three players"), self._dialog)
        threeButton.clicked.connect(self.threePlayers)
        fourButton = QPushButton(QCoreApplication.translate("play", "Four players"), self._dialog)
        fourButton.clicked.connect(self.fourPlayers)
        fiveButton = QPushButton(QCoreApplication.translate("play", "Five players"), self._dialog)
        fiveButton.clicked.connect(self.fivePlayers)

        layout.addWidget(lineEdit)
        layout.addWidget(threeButton)
        layout.addWidget(fourButton)
        layout.addWidget(fiveButton)

        self._dialog.setLayout(layout)

        self._dialog.exec()

        if (self._dialog.result() == QDialog.Rejected):
            return

        if (self._playerNumber == 3):
            self._globalRatio = 0.85
        elif (self._playerNumber == 4):
            self._globalRatio = 0.9
        elif (self._playerNumber == 5):
            self._globalRatio = 0.8

        self._cardSize = (int(56 * self._globalRatio), int(109 * self._globalRatio))

        self._client = Client(self, self._playerNumber)

        self._window = Window(self)
        self._window.setWindowTitle(QCoreApplication.translate("play", "Tarot"))

        self._tableLabel = TableLabel.TableLabel(self._window)
        self._pointsLabel = QLabel(QCoreApplication.translate("play", "Attack points: 0 - Defence points: 0"), self._window)
        self._pointsLabel.setAlignment(Qt.AlignCenter)

        self._contractLabel = QLabel(QCoreApplication.translate("play", "Choose a contract"), self._window)
        self._contractLabel.setVisible(False)
        self._contractComboBox = QComboBox(self._window)
        self._contractComboBox.setVisible(False)

        choices = []

        for i in range(0, 4):
            choices.append(str(Family.Family(i)))

        self._kingLabel = QLabel(QCoreApplication.translate("play", "Call a king"), self._window)
        self._kingLabel.setVisible(False)
        self._kingComboBox = QComboBox(self._window)
        self._kingComboBox.addItems(choices)
        self._kingComboBox.setVisible(False)

        self._dogLabel = QLabel(QCoreApplication.translate("play", "Do a dog"), self._window)
        self._dogLabel.setVisible(False)
        self._dogComboBoxes = []
        for i in range(0, 6):
            self._dogComboBoxes.append(QComboBox(self._window))
            self._dogComboBoxes[-1].setVisible(False)
            self._dogComboBoxes[-1].activated.connect(self.comboBoxActivated)

        self._cardLabel = QLabel(QCoreApplication.translate("play", "Play a card"), self._window)
        self._cardLabel.setVisible(False)
        self._cardComboBox = QComboBox(self._window)
        self._cardComboBox.setVisible(False)

        okButton = QPushButton(QCoreApplication.translate("play", "OK"), self._window)
        okButton.clicked.connect(self.ok)
        shortcut = QShortcut(QKeySequence(Qt.Key_Return), okButton)
        shortcut.activated.connect(okButton.click)

        verticalLayout = QVBoxLayout()
        verticalLayout.addWidget(self._contractLabel)
        verticalLayout.addWidget(self._contractComboBox)
        verticalLayout.addWidget(self._kingLabel)
        verticalLayout.addWidget(self._kingComboBox)
        verticalLayout.addWidget(self._dogLabel)
        self._dogIndex = 0
        for i in range(0, 6):
            verticalLayout.addWidget(self._dogComboBoxes[i])
        verticalLayout.addWidget(self._cardLabel)
        verticalLayout.addWidget(self._cardComboBox)
        verticalLayout.addWidget(okButton)

        horizontalLayout = QHBoxLayout()
        layout = QVBoxLayout()

        layout.addWidget(self._tableLabel)
        layout.addWidget(self._pointsLabel)
        horizontalLayout.addLayout(layout)        
        horizontalLayout.addLayout(verticalLayout)

        self._window.setLayout(horizontalLayout)

        self._timer = QTimer(self._window)
        self._timer.setInterval(10)
        self._timer.timeout.connect(self.monitor)
        self._timer.start()
        
        self._centerTimer = QTimer(self._window)
        self._centerTimer.setInterval(500)
        self._centerTimer.setSingleShot(True)
        self._centerTimer.timeout.connect(self.centerWindow)
        self._centerTimer.start()

    def centerWindow(self):
        self._window.show()
        
        screen_geometry = QApplication.desktop().availableGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        window_width = self._window.width()
        window_height = self._window.height()

        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        self._window.move(x, y)
    
    def ok(self):
        self._ok = True
        
    def monitor(self):
        if (self._gameData == None):
            return
        
        if (self._gameData._gameState == Game.GameState.Begin
            or self._gameData._gameState == Game.GameState.End):
            self.displayTable([])
        elif (self._gameData._gameState == Game.GameState.ChooseContract
              or self._gameData._gameState == Game.GameState.CallKing):
            self.displayTable(self._gameData._dog, False, True)
        elif (self._gameData._gameState == Game.GameState.ShowDog):
            self.displayTable(self._gameData._dog, True)
        elif (self._gameData._gameState == Game.GameState.DoDog):
            self.displayTable([], False, True)
        
        take = ""
        
        if (self._gameData._calledKing):
            take = QCoreApplication.translate("monitor", "\nCalled king: ") \
                   + str(self._game._calledKing)

        if (self._gameData._contract):
            take += QCoreApplication.translate("monitor", "\nContract: ") \
                    + str(self._gameData._contract) \
                    + QCoreApplication.translate("play", " ({0} points)") \
                    .format(self._gameData.attackTargetPoints())
    
        self._pointsLabel.setText(QCoreApplication.translate("monitor",
                                                             "Attack points: {0} - Defence points: {1}")
                                  .format(self._gameData.attackPoints(),
                                          self._gameData.defencePoints())
                                  + take)
                                  
        if (self._tableLabel._mousePressPos):
            for i in range(0, self._gameData._playerNumber):
                if (i == self._gameData._currentPlayer):
                    radius = common.playerRadius(self._gameData._playerNumber, self._globalRatio)
                    
                    positions = [(self._tableLabel.pixmap().width() // 2,
                                  self._tableLabel.pixmap().height() // 2 + radius)]
                    angles = [0]

                    for k in range(1, self._playerNumber):
                        angles.append(angles[-1] - 360 / self._playerNumber)
                        x = self._tableLabel.pixmap().width() / 2 + radius * math.sin(math.radians(angles[-1]))
                        y = self._tableLabel.pixmap().height() / 2 + radius * math.cos(math.radians(angles[-1]))
                        positions.append((x, y))

                    n = len(self._gameData._players[i]._cards)
                    w = (n - 1) * self._cardSize[0] * self._overCardRatio + self._cardSize[0]

                    for j in range(0, n):
                        rect = QRectF(int(j * self._cardSize[0] * self._overCardRatio), 0, self._cardSize[0] * (1 if j == n - 1 else self._overCardRatio), self._cardSize[1])
                        transform = QTransform()
                        transform.translate(rect.center().x(), rect.center().y())
                        transform.rotate(angles[i])
                        transform.translate(-rect.center().x(), -rect.center().y())
                        transform.translate(positions[i][0] - w / 2,
                                            positions[i][1] - self._cardSize[1] / 2)
        
                        points = [transform.map(rect.topLeft()),
                                  transform.map(rect.topRight()),
                                  transform.map(rect.bottomRight()),
                                  transform.map(rect.bottomLeft()),
                                  transform.map(rect.topLeft())]
                        
                        polygon = QPolygonF(points)
                       
                        if (polygon.containsPoint(self._tableLabel._mousePressPos, Qt.WindingFill)):
                            enabledCards = []
                        
                            enabledCards = self._gameData._players[i].enabledCards(self._gameData._centerCards,
                                                                                   self._gameData._firstRound,
                                                                                   self._gameData._calledKing,
                                                                                   self._dogLabel.isVisible())

                            if (enabledCards[j]):
                                if (self._cardComboBox.isVisible()):
                                    self._cardComboBox.setCurrentText(self._gameData._players[i]._cards[j].name())
                                elif (self._dogLabel.isVisible()):
                                    self._tableLabel._mousePressPos = None
                                    self._dogComboBoxes[self._dogIndex].setCurrentText(self._gameData._players[i]._cards[j].name())
                                    self._dogIndex += 1
                                    if (self._dogIndex >= 6 or not self._dogComboBoxes[self._dogIndex].isVisible()):
                                        self._dogIndex = 0
                            
                            break

                    break
    
        if (self._gameData._gameState == Game.GameState.End):
            if (self._gameData.attackPoints() == 0
                and self._gameData.defencePoints() == 0):
                QMessageBox.information(self._window,
                                        QCoreApplication.translate("monitor", "Game over"),
                                        QCoreApplication.translate("monitor", "Nobody takes!"))
                
                self._window.close()
            else:
                if (self._gameData.attackWins()):
                    QMessageBox.information(self._window,
                                            QCoreApplication.translate("monitor", "Game over"),
                                            (QCoreApplication.translate("monitor", "Well done!") if self._gameData._players[0].attackTeam() else QCoreApplication.translate("monitor", "Shame!"))
                                            + QCoreApplication.translate("monitor", " Attack wins ({0} points for {1} points)!")
                                            .format(self._gameData.attackPoints(),
                                                    self._gameData.attackTargetPoints()))
                else:
                    QMessageBox.information(self._window,
                                            QCoreApplication.translate("monitor", "Game over"),
                                            (QCoreApplication.translate("monitor", "Well done!") if self._gameData._players[0].defenceTeam() else QCoreApplication.translate("monitor", "Shame!"))
                                            + QCoreApplication.translate("monitor", " Attack loses ({0} points for {1} points)!")
                                            .format(self._gameData.attackPoints(),
                                                    self._gameData.attackTargetPoints()))

                self._window.close()
