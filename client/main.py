import json.decoder
import sys
import requests
from PyQt5.QtCore import QObject, pyqtProperty, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine, QQmlListProperty
from threading import Timer, Lock

server_address = "http://127.0.0.1:5000"


class Message(QObject):
    def __init__(self, msg: str, author: int, parent=None) -> None:
        super().__init__(parent)
        self._msg = msg
        self._author = author

    @pyqtProperty('QString', constant=True)
    def msg(self) -> str:
        return self._msg

    @pyqtProperty(int, constant=True)
    def author(self) -> int:
        return self._author


# noinspection PyUnresolvedReferences
class ClientModel(QObject):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._message_list = [Message('aa', 0), Message('bb', 1)]
        self._lock = Lock()

        self._token = None
        self._have_login = False
        self._timer = None
        self._time_count = None
        self.connect()

    def __del__(self) -> None:
        if self._timer is not None:
            self._timer.cancel()

    message_list_changed = pyqtSignal()
    have_login_changed = pyqtSignal()

    @pyqtProperty(QQmlListProperty, notify=message_list_changed)
    def message_list(self) -> QQmlListProperty:
        return QQmlListProperty(Message, self, self._message_list)

    @pyqtProperty(bool, notify=have_login_changed)
    def have_login(self) -> bool:
        return self._have_login

    def append_message(self, msg: Message) -> None:
        self._message_list.append(msg)
        self.message_list_changed.emit()

    @pyqtSlot('QString')
    def submit_message(self, msg: str) -> None:
        if self._token is None:
            self.connect()
            if self._token is None:
                return

        if len(msg.strip()) == 0:
            return
        self.append_message(Message(msg, 1))

        with self._lock:
            self._time_count = 0
        self._timer.cancel()
        self._timer = Timer(5, self.timeout_handler)
        self._timer.start()

        try:
            r = requests.get(server_address + '/send', params={"token": self._token, "msg": msg})
            if r.status_code == 401:
                self.append_message(Message("需要登录，请点击右上角登录", 0))
                return
            elif r.status_code == 403:
                self.append_message(Message("服务器拒绝请求，请重启客户端", 0))
                self._timer.cancel()
                return
            elif r.status_code != 200:
                raise requests.exceptions.ConnectionError()
            for msg in r.json().get("msg"):
                self.append_message(Message(msg, 0))
            if r.json().get("exit"):
                self.append_message(Message("会话结束，您可以发送一条消息开始新的会话", 0))
                self._token = None
                self._have_login = False
                self._timer.cancel()
        except requests.exceptions.ConnectionError:
            self.append_message(Message("服务器异常，请稍后重试", 0))
        except (KeyError, json.decoder.JSONDecodeError):
            self.append_message(Message("服务器消息异常，请稍后重试", 0))

    @pyqtSlot('QString', 'QString')
    def user_login(self, username: str, passwd: str) -> None:
        if self._token is None:
            self.connect()
            if self._token is None:
                self.append_message(Message("服务器异常，请稍后重试", 0))
                return
        try:
            r = requests.get(server_address + '/login',
                             params={"token": self._token, "username": username, "passwd": passwd})
            if r.status_code == 403:
                self.append_message(Message("服务器拒绝请求，请重启客户端", 0))
                self._timer.cancel()
                return
            elif r.status_code != 200:
                raise requests.exceptions.ConnectionError()
            if r.json().get("token") is None:
                self.append_message(Message("登录失败，用户名或密码无效", 0))
                return
            self._token = r.json().get("token")
            self.append_message(Message("登录成功", 0))
        except requests.exceptions.ConnectionError:
            self.append_message(Message("服务器异常，请稍后重试", 0))
        except (KeyError, json.decoder.JSONDecodeError):
            self.append_message(Message("服务器消息异常，请稍后重试", 0))

    @pyqtSlot('QString', 'QString')
    def user_register(self, username: str, passwd: str) -> None:
        if self._token is None:
            self.connect()
            if self._token is None:
                self.append_message(Message("服务器异常，请稍后重试", 0))
                return
        try:
            r = requests.get(server_address + '/register',
                             params={"token": self._token, "username": username, "passwd": passwd})
            if r.status_code == 403:
                self.append_message(Message("服务器拒绝请求，请重启客户端", 0))
                self._timer.cancel()
                return
            elif r.status_code != 200:
                raise requests.exceptions.ConnectionError()
            self._token = r.json().get("token")
            self.append_message(Message("注册并登录成功", 0))
        except requests.exceptions.ConnectionError:
            self.append_message(Message("服务器异常，请稍后重试", 0))
        except (KeyError, json.decoder.JSONDecodeError):
            self.append_message(Message("服务器消息异常，请稍后重试", 0))

    def connect(self) -> None:
        try:
            r = requests.get(server_address)
            if r.status_code != 200:
                raise requests.exceptions.ConnectionError()
            self._token = r.json().get("token")
            for msg in r.json().get("msg"):
                self.append_message(Message(msg, 0))
        except requests.exceptions.ConnectionError:
            self.append_message(Message("服务器异常，请稍后重试", 0))
        except KeyError:
            self.append_message(Message("服务器消息异常，请稍后重试", 0))
        self._time_count = 0
        self._timer = Timer(5, self.timeout_handler)
        self._timer.start()

    def timeout_handler(self) -> None:
        with self._lock:
            self._time_count += 5
        self._timer = Timer(5, self.timeout_handler)
        self._timer.start()

        try:
            r = requests.get(server_address + '/echo', params={"token": self._token, "seconds": self._time_count})
            if r.status_code == 401:
                self.append_message(Message("需要登录，请点击右上角登录", 0))
                return
            elif r.status_code == 403:
                self.append_message(Message("服务器拒绝请求，请重启客户端", 0))
                self._timer.cancel()
                return
            elif r.status_code != 200:
                raise requests.exceptions.ConnectionError()
            if r.json().get("reset"):
                with self._lock:
                    self._time_count = 0
            for msg in r.json().get("msg"):
                self.append_message(Message(msg, 0))
            if r.json().get("exit"):
                self.append_message(Message("会话结束，您可以发送一条消息开始新的会话", 0))
                self._token = None
                self._have_login = False
                self._timer.cancel()
        except requests.exceptions.ConnectionError:
            self.append_message(Message("服务器异常，请稍后重试", 0))
        except (KeyError, json.decoder.JSONDecodeError):
            self.append_message(Message("服务器消息异常，请稍后重试", 0))


if __name__ == '__main__':
    app = QGuiApplication(sys.argv)

    engine = QQmlApplicationEngine()
    client_model = ClientModel()
    engine.rootContext().setContextProperty("client_model", client_model)
    engine.load('main.qml')
    # user_button = engine.rootObjects()[0].children()[2].children()[2]
    # user_button.setProperty("visible", False)

    app.exec()
    client_model.__del__()
