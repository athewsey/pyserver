#! /usr/bin/env bash
python3 -m venv pyenv
pyenv/bin/pip install aiohttp
pyenv/bin/pip install asyncio
pyenv/bin/pip install cchardet
pyenv/bin/pip install pyjwt

pyenv/bin/python3 server
