#! /usr/bin/env python3
from aiohttp import web
from datetime import datetime, timedelta
import json
import jwt
import os

from Gomoku import Client as GomokuClient, Session as GomokuSession

JWT_SECRET = "secret"
JWT_ALGORITHM = "HS512"
JWT_EXPIRY_SECONDS = 20

GOMOKU_HOST = "hub.nechifor.net:8443"
GOMOKU_DEFAULT_GAMES = 1
GOMOKU_DEFAULT_ROOM = "101"
GOMOKU_USER_AGENT = "Gomugi (by Alex)"

async def login(req):
    post_data = await req.post()
    try:
        assert post_data["id"] == "user"
        assert post_data["password"] == "password"
    except (KeyError, AssertionError):
        return web.json_response(
            { "message": "Incorrect credentials" },
            status=400
        )
    payload = {
        "id": "user",
        "expires": (datetime.utcnow() + timedelta(seconds=JWT_EXPIRY_SECONDS)).isoformat()
    }
    jwt_token = jwt.encode(payload, JWT_SECRET, JWT_ALGORITHM)
    return web.json_response({ "token": jwt_token.decode("utf-8") })

async def test(req):
    name = "Anonymous"
    try:
        name = req.query["name"]
    except KeyError:
        pass
    text = "Hello, " + name
    return web.json_response(text)


async def play(req):
    """Sign in to a room and play a Gomoku game
    """
    room = req.query.get("room") or GOMOKU_DEFAULT_ROOM
    games = req.query.get("games") or GOMOKU_DEFAULT_GAMES
    await GomokuClient(GOMOKU_HOST, GOMOKU_USER_AGENT).play_game(room, games)
    return web.json_response({ "success": True })


async def train(req):
    """Play a Gomoku game against myself to train
    """

    players = [
        GomokuClient(GOMOKU_HOST, GOMOKU_USER_AGENT),
        GomokuClient(GOMOKU_HOST, GOMOKU_USER_AGENT)
    ]
    session = GomokuSession(GOMOKU_DEFAULT_ROOM, players)
    await session.run()
        
    return web.json_response({ "success": True })

app = web.Application()

app.router.add_post("/login", login)
app.router.add_get("/test", test)
app.router.add_get("/play", play)
app.router.add_get("/train", train)
app.router.add_static(
    "/",
    os.path.abspath(os.path.join("client"))
)

web.run_app(app)
