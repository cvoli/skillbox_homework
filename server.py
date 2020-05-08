"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                temp_login = decoded.replace("login:", "").replace("\r\n", "")
                for client in self.server.clients:
                    if client.login == temp_login:
                        self.transport.write(
                            f'Логин {temp_login} занят, попробуйте другой'.encode()
                        )
                        self.transport.abort()
                        break
                self.login = temp_login
                self.transport.write(
                        f"Привет, {self.login}!\n".encode()
                    )
                self.send_history()
        else:
            self.send_message(decoded)

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()
        self.server.history.append(format_string)
        if len(self.server.history)>10:
            self.server.history.pop(0)
        for client in self.server.clients:
            if client.login != self.login and client.login is not None:
                client.transport.write(encoded)

    def send_history(self):
        history_size = len(self.server.history)
        if history_size > 0:
            self.transport.write(
                f"История чата, всего {history_size}):\n".encode()
            )
            for history_message in self.server.history:
                self.transport.write(
                    f"{history_message}\n".encode()
                )
        else:
            self.transport.write(
                f"В чате не было сообщений\n".encode()
            )

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []
        self.history = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
