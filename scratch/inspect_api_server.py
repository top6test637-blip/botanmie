from aiogram.client.telegram import TelegramAPIServer
import inspect

print("TelegramAPIServer __init__ signature:")
print(inspect.signature(TelegramAPIServer.__init__))

print("\nTelegramAPIServer.from_base signature:")
print(inspect.signature(TelegramAPIServer.from_base))
