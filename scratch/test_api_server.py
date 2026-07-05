from aiogram.client.telegram import TelegramAPIServer

api_server = TelegramAPIServer.from_base("http://localhost:8081")
print(f"from_base('http://localhost:8081') is_local: {api_server.is_local}")

api_server_2 = TelegramAPIServer.from_base("http://localhost:8081", is_local=False)
print(f"from_base('http://localhost:8081', is_local=False) is_local: {api_server_2.is_local}")
