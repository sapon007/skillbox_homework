"""
Серверное приложение
"""
import asyncio
from asyncio import transports


# Класс протокола клиента наследуется от asyncio.Protocol
class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    # transports какая-то абстракция для socket, Transport - TCP
    transport: transports.Transport

    # Конструктор класса
    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    # Метод, который вызывается, когда какие-то данные были получены (переопределенный метод)
    def data_received(self, data: bytes):
        # Декодируем данные из бинарного вида
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            if decoded.startswith("login:"):
                # login:user
                login = decoded.replace("login:", "").replace("\r\n", "")
                # Проверяем есть ли уже такой пользователь (возможно можно было обойтись без цикла, но пока не придумал)
                for client in self.server.clients:
                    if client.login == login:
                        self.transport.write(
                            f"Логин {self.login} занят, попробуйте другой".encode()
                        )
                        self.transport.close() # Закрываем соединение
                self.login = login
                self.transport.write(
                    f"Привет, {self.login}!".encode()
                )
                # Выводим историю сообщений для нового пользователя, если она имеется
                if len(self.server.messages) > 0:
                    self.send_history(self.server.messages)
        else:
            # Храним историю сообщений
            self.server.messages.append(decoded)
            self.send_message(decoded)

    # Метод, формирующий сообщение для отправки клиентам
    def send_message(self, message):
        format_string = f"<{self.login}>: {message}"
        # Кодируем строку для передачи в бинарном виде
        encoded = format_string.encode()

        # Передаем сообщение всем клиентам, кроме себя
        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    # Метод, отсылающий последние 10 сообщений
    def send_history(self, data: list):
        # Передаем историю сообщений только себя
        history_string = "Последние сообщения в чате:\r\n"
        self.transport.write(history_string.encode())
        if len(data) > 10:
            # Определяем с какого индекса выполнить срез чтобы вывести последние 10 сообщений
            len_history = len(data) - 10
            for message in data[len_history:]:
                message = message + "\r\n"
                self.transport.write(message.encode())
        else:
            for message in data:
                message = message + "\r\n"
                self.transport.write(message.encode())

    # Вызывается, когда соединение устанавливается (переопределенный метод)
    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    # Вызывается, когда соединение разрывается (переопределенный метод)
    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server:
    # Список клиентов, подключенных к серверу
    clients: list
    # Храним список сообщений
    messages: list

    # конструктор класса, создает пустой список клиентов
    def __init__(self):
        self.clients = []
        self.messages = []

    def create_protocol(self):
        return ClientProtocol(self)

    # Стартуем сервер
    async def start(self):
        # Получаем все запущенные события
        loop = asyncio.get_running_loop()

        # Создаем TCP сервер
        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен...")

        # Принимаем соединения, пока не остановим сервер
        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
