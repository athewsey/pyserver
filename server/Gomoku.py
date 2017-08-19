""" Client for Gomoku
"""
# PIP Dependencies:
import asyncio
import numpy as np

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
        "board_size": 15
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
            # Temp: move to last empty area on board (bottom right)
            target = np.argwhere(self.board == 0)[-1]
            # Flatten index & request the move:
            print("Player {} moving to {}".format(self.player_ix, target))
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
