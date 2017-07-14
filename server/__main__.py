#! /usr/bin/env python3
from aiohttp import web

async def handle(req):
    name = "Anonymous"
    try:
        name = req.query["name"]
    except KeyError:
        pass
    text = "Hello, " + name
    return web.json_response(text)

app = web.Application()
app.router.add_get("/", handle)

web.run_app(app)
