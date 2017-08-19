""" Client for Gomoku
"""
from AoireClient import AoireClient
import asyncio
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
    
    async def join(self, room, nGames=1):
        """Join a room
        """
        joinedMsg = await super().join(AOIRE_GAME_TYPE, room, nGames, self.userAgent)
        self.playerIx = joinedMsg["index"]

    async def start(self):
        """Wait for a game to start in the current room
        """
        startedMsg = await self.recv()
        assert startedMsg["type"] == "Started"
        self.board = np.array([[0] * self.board_size] * self.board_size, dtype=np.float64)
        return startedMsg
    
    async def turn(self, playerIx):
        """Make a move if it's my turn; listen for and process turn state update
        """
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

    # TODO: Fix duplication of nGames default param
    async def play_game(self, room, nGames=1):
        results = []
        await self.join(room, nGames)
        for ixGame in range(nGames):
            startMsg = await self.start()
            result = None
            startingPlayerIx = startMsg["playerIndex"]
            activePlayerIx = startingPlayerIx
            while result is None:
                result = await self.turn(activePlayerIx)
                # 2 player game:
                activePlayerIx = int(not activePlayerIx)
            result["startingPlayerIx"] = startingPlayerIx
            results.append(result)
        
        return {
            "userAgent": self.userAgent,
            "playerIx": self.playerIx,
            "results": results
        }

class Session:
    def __init__(self, roomName, players, nGames=5):
        self.room = roomName
        self.nGames = nGames
        assert len(players) == 2, "A list of exactly 2 players is required"
        self.players = players
    
    async def run(self):
        donePlayTasks, pending = await asyncio.wait([player.play_game(self.room, self.nGames) for player in self.players])
        return list(filter(lambda x: x["playerIx"] == 0, [playTask.result() for playTask in donePlayTasks]))[0]
