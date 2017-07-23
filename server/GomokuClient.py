""" Client for Gomoku
"""
from AoireClient import AoireClient
import numpy as np

AOIRE_GAME_TYPE = "Gomoku"

class GomokuClient(AoireClient):
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

    def __init__(self, url, board_size=15):
        """Class constructor
        """
        self.board_size = board_size
        super().__init__(url)
    
    async def join(self, room, userAgent=None):
        joinedMsg = await super().join(AOIRE_GAME_TYPE, room, 1, userAgent)
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