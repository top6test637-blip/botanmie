import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from aiogram import Bot
import inspect
from config import config

bot = Bot(token=config.BOT_TOKEN)
sig = inspect.signature(bot.send_video)
print("send_video parameters:")
for p in sig.parameters:
    print(p)
