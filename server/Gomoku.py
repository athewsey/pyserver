""" Client for Gomoku
"""
# PIP Dependencies:
import asyncio
import math
import numpy as np
from timeit import default_timer as timer

# Local Dependencies:
from AoireClient import AoireClient


class Agent(AoireClient):
    """Client for Gomoku game
    """

    agent_config = {
        "author": "Alex",
        "name": "Gomugi",
        "version": "0.1.0"
    }

    game_config = {
        "aoire_game_type": "Gomoku",
        "board_size": 15,
        "move_time_limit": 1.0 # seconds
    }
    
    """
        +1 for our piece, -1 for opponent, 0 for empty, floats used to enable easy convolution and
        because representation of 0/+-1 will be perfect
    """
    board = np.array([[]], dtype=np.float64)

    """0 = black, 1 = white
    """
    player_ix = None

    def __init__(self, url, agent_config=None, game_config=None):
        """Class constructor
        """
        if (agent_config is not None):
            self.agent_config = agent_config
        if (game_config is not None):
            self.game_config = game_config
        
        super().__init__(url)
    
    async def join(self, room, n_games=1):
        """Join a room
        """
        joined_msg = await super().join(
            self.game_config["aoire_game_type"],
            room,
            n_games,
            self.user_agent()
        )
        self.player_ix = joined_msg["index"]

    async def start(self):
        """Wait for a game to start in the current room
        """
        started_msg = await self.recv()
        assert started_msg["type"] == "Started"
        self.board = np.array(
            [[0] * self.game_config["board_size"]] * self.game_config["board_size"],
            dtype=np.float64
        )
        return started_msg
    
    async def turn(self, player_ix):
        """Make a move if it's my turn; listen for and process turn state update
        """
        my_turn = player_ix == self.player_ix
        if (my_turn):
            # Our turn to move
            t_start = timer()
            target = await self.select_move()
            # Flatten index & request the move:
            print("Player {} moving to {} ({}ms)".format(
                self.player_ix, target, (timer() - t_start) * 1000
            ))
            await self.send({
                "type": "Move",
                "move": int(np.ravel_multi_index(target, self.board.shape))
            })
        
        # Regardless of whose turn happened, we will receive a state update message:
        state_update = await self.recv()
        move_target = state_update["move"]
        assert(self.board.flat[move_target] == 0)
        self.board.flat[move_target] = 1 if my_turn else -1

        if ("winner" in state_update):
            return { "result": state_update["winner"] == self.player_ix }
        else:
            return None

    # TODO: Fix duplication of n_games default param
    async def play_game(self, room, n_games=1):
        results = []
        await self.join(room, n_games)
        for ixGame in range(n_games):
            start_msg = await self.start()
            result = None
            starting_ix = start_msg["playerIndex"]
            active_ix = starting_ix
            while result is None:
                result = await self.turn(active_ix)
                # 2 player game:
                active_ix = int(not active_ix)
            result["startingPlayerIx"] = starting_ix
            results.append(result)
        
        return {
            "user_agent": self.user_agent(),
            "player_ix": self.player_ix,
            "results": results
        }
    
    def user_agent(self):
        result = self.agent_config["name"]
        if (self.agent_config["version"]):
            result = result + " v" + self.agent_config["version"]
        
        return result + " (by " + \
            (self.agent_config["author"] if self.agent_config["author"] else "Anonymous") + ")"
    
    async def select_move(self):
        t_start = timer()
        options = [{ "coords": coords, "score": 0 } for coords in np.argwhere(self.board == 0)]
        # A crappy first guess (last empty square):
        selection = options[-1]
        timed_out = (timer() - t_start) >= self.game_config["move_time_limit"]

        n_options = len(options)
        board_size = self.game_config["board_size"]
        N_DIMS = 2 # 2-D board
        search_dirs = cartesian([[-1, 0, 1]] * N_DIMS)
        # Remove the null [0, 0] search direction:
        search_dirs = search_dirs[search_dirs.any(axis=1)]
        next_options = []
        ix_opt = 0
        while (not timed_out and ix_opt < n_options):
            opt = options[ix_opt]
            searches = [{
                "dir": dir,
                "lim": int(np.min([
                    opt["coords"][ix_dim] if dir[ix_dim] < 0 else (
                        board_size - 1 - opt["coords"][ix_dim] if dir[ix_dim] > 0 else math.inf
                    )
                    for ix_dim in range(N_DIMS)
                ]))
            } for dir in search_dirs]
            for search in searches:
                run = 0
                pos = opt["coords"]
                for step in range(search["lim"]):
                    newPos = np.add(pos, search["dir"])
                    # Need to use a tuple to index the board, not a list as argwhere returns:
                    if self.board[tuple(newPos)] == 1:
                        run += 1
                    else:
                        break
                search["run"] = run
            opt["score"] = np.max([search["run"] for search in searches])
            if opt["score"] > selection["score"]:
                selection = opt        
            
            ix_opt += 1
            timed_out = (timer() - t_start) >= self.game_config["move_time_limit"]
        
        return selection["coords"]


class Session:
    def __init__(self, room, players, n_games=4):
        self.room = room
        self.n_games = n_games
        assert len(players) == 2, "A list of exactly 2 players is required"
        self.players = players
    
    async def run(self):
        done_play_tasks, pending = await asyncio.wait(
            [player.play_game(self.room, self.n_games) for player in self.players]
        )
        return list(filter(lambda x: x["player_ix"] == 0, [task.result() for task in done_play_tasks]))[0]


def cartesian(arrays, out=None):
    """
    Generate a cartesian product of input arrays.
    https://stackoverflow.com/questions/1208118/using-numpy-to-build-an-array-of-all-combinations-of-two-arrays

    Parameters
    ----------
    arrays : list of array-like
        1-D arrays to form the cartesian product of.
    out : ndarray
        Array to place the cartesian product in.

    Returns
    -------
    out : ndarray
        2-D array of shape (M, len(arrays)) containing cartesian products
        formed of input arrays.

    Examples
    --------
    >>> cartesian(([1, 2, 3], [4, 5], [6, 7]))
    array([[1, 4, 6],
           [1, 4, 7],
           [1, 5, 6],
           [1, 5, 7],
           [2, 4, 6],
           [2, 4, 7],
           [2, 5, 6],
           [2, 5, 7],
           [3, 4, 6],
           [3, 4, 7],
           [3, 5, 6],
           [3, 5, 7]])

    """

    arrays = [np.asarray(x) for x in arrays]
    dtype = arrays[0].dtype

    n = np.prod([x.size for x in arrays])
    if out is None:
        out = np.zeros([n, len(arrays)], dtype=dtype)

    m = int(n / arrays[0].size)
    out[:,0] = np.repeat(arrays[0], m)
    if arrays[1:]:
        cartesian(arrays[1:], out=out[0:m,1:])
        for j in range(1, arrays[0].size):
            out[j*m:(j+1)*m,1:] = out[0:m,1:]
    return out