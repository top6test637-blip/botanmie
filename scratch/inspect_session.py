from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.methods import SendVideo
from aiogram.types import FSInputFile
import inspect

# Inspect how files are prepared
session = AiohttpSession(api=TelegramAPIServer.from_base("http://localhost:8081"))
print("AiohttpSession.make_request signature:")
print(inspect.signature(session.make_request))

# Inspect source code of session.make_request or how it checks is_local
try:
    source = inspect.getsource(session.make_request)
    print("\nmake_request source snippet:")
    print("\n".join(source.split("\n")[:40]))
except Exception as e:
    print(f"Error getting source: {e}")
