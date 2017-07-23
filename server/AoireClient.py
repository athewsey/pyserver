import aiohttp
import json

class AoireClient:
    def __init__(self, host):
        self.host = host
        self.session = aiohttp.ClientSession()
        self._ws = None

    async def connected(self):
        if (not self._ws):
            self._ws = await self.session.ws_connect("ws://{}/game".format(self.host))
        
        return self._ws
        
    async def send(self, msg):
        ws = await self.connected()
        return await ws.send_str(json.dumps(msg))

    async def recv(self):
        ws = await self.connected()
        rawMsg = await ws.receive()
        if (rawMsg.tp != aiohttp.WSMsgType.TEXT):
            print(aiohttp.WSMsgType.TEXT)
            print(rawMsg.tp)
            print(json.dumps(rawMsg))
        assert rawMsg.tp == aiohttp.WSMsgType.TEXT
        print(rawMsg.data)
        return json.loads(rawMsg.data)

    async def join(self, gameType, room, nGames=5, userAgent=None):
        msg = {
            "type": "StartGame",
            "gameType": gameType,
            "room": room,
            "nGames": nGames
        }

        if (userAgent is not None):
            msg["userAgent"] = userAgent

        await self.send(msg)
        # Wait for the YouAre message before returning.
        # YouAre is pretty much just an ack - Started will give us our player index again anyway
        joinedMsg = await self.recv()
        assert joinedMsg["type"] == "YouAre"
        return joinedMsg