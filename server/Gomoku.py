""" Client for Gomoku
"""
from AoireClient import AoireClient
import numpy as np

AOIRE_GAME_TYPE = "Gomoku"

class Client(AoireClient):
    """Client for Gomoku game
    """

    board_size = 0
    """
        +1 for our piece, -1 for opponent, 0 for empty, floats used to enable easy convolution and
        because representation of 0/+-1 will be perfect
    """
    board = np.array([[]], dtype=np.float64)

    """0 = black, 1 = white
    """
    playerIx = None

    """(Optional) identifier for this client
    """
    userAgent = None

    def __init__(self, url, userAgent=None, board_size=15):
        """Class constructor
        """
        self.board_size = board_size
        self.userAgent = userAgent
        super().__init__(url)
    
    async def join(self, room):
        joinedMsg = await super().join(AOIRE_GAME_TYPE, room, 1, self.userAgent)
        self.playerIx = joinedMsg["index"]

    async def start(self):
        startedMsg = await self.recv()
        assert startedMsg["type"] == "Started"
        self.board = np.array([[0] * self.board_size] * self.board_size, dtype=np.float64)
        return startedMsg
    
    async def turn(self, playerIx):
        myTurn = playerIx == self.playerIx
        if (myTurn):
            # Our turn to move
            # Temp: move to last empty area on board (bottom right)
            target = np.argwhere(self.board == 0)[-1]
            # Flatten index & request the move:
            print("Player {} moving to {}".format(self.playerIx, target))
            await self.send({
                "type": "Move",
                "move": int(np.ravel_multi_index(target, self.board.shape))
            })
        
        # Regardless of whose turn happened, we will receive a state update message:
        stateUpdate = await self.recv()
        moveTarget = stateUpdate["move"]
        assert(self.board.flat[moveTarget] == 0)
        self.board.flat[moveTarget] = 1 if myTurn else -1

        if ("winner" in stateUpdate):
            return { "result": stateUpdate["winner"] == self.playerIx }
        else:
            return None


class Session:
    def __init__(self, roomName, players):
        self.room = roomName
        assert len(players) == 2, "A list of exactly 2 players is required"
        self.players = players

    async def run(self):
        # Join both players to the room:
        for player in self.players:
            await player.join(self.room)
        
        # Wait for server game ready & capture one start message (doesn't matter which) to tell us
        # which player will go first:
        startMsg = None
        for player in self.players:
            startMsg = await player.start()
        
        # Take turns until the game is finished:
        result = None
        activePlayerIx = startMsg["playerIndex"]
        while result is None:
            activePlayer = next(
                player for player in self.players if player.playerIx == activePlayerIx
            )
            otherPlayers = [player for player in self.players if player is not activePlayer]
            
            # Active player takes turn first to actually perform the action:
            # (turn returns None unless the game is over)
            result = await activePlayer.turn(activePlayerIx)
            # Other players process updates:
            for player in otherPlayers:
                await player.turn(activePlayerIx)
            
            activePlayerIx = (activePlayerIx + 1) % len(self.players)

        return result
