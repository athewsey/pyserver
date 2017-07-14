#! /usr/bin/env python3
from aiohttp import web
from datetime import datetime, timedelta
import jwt
import os

JWT_SECRET = "secret"
JWT_ALGORITHM = "HS512"
JWT_EXPIRY_SECONDS = 20

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

app = web.Application()

app.router.add_post("/login", login)
app.router.add_get("/test", test)
app.router.add_static(
    "/",
    os.path.abspath(os.path.join("client"))
)

web.run_app(app)
