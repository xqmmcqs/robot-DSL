import time
from typing import Any
from threading import Lock, Timer
import jwt
from server.state_machine import UserState


class User:
    def __init__(self, username: str) -> None:
        self.timer = None
        self.state = UserState()
        self.username = username


class UserManage:
    def __init__(self, key="this_is_a_secret") -> None:
        self.users: dict[str, User] = dict()
        self.lock = Lock()
        self.key = key

    def jwt_encode(self, username: str) -> str:
        return jwt.encode({"username": username}, self.key, algorithm="HS256")

    def jwt_decode(self, token: str) -> User:
        username = jwt.decode(token, self.key, algorithms="HS256").get("username")
        if username is None or username not in self.users.keys():
            raise jwt.InvalidTokenError
        return self.users[username]

    def connect(self) -> (User, str):
        username = f"Guest_{time.time_ns()}"
        with self.lock:
            self.users[username] = User(username)
            self.users[username].timer = Timer(300, self.timeout_handler, username)
        return self.users[username], self.jwt_encode(username)

    def login(self, user: User, username: str, passwd: str) -> Any:
        old_username = user.username
        if not self.users[old_username].state.login(username, passwd):
            return None
        with self.lock:
            self.users[username] = self.users[old_username]
            self.users[username].username = username
            del self.users[old_username]
        return self.jwt_encode(username)

    def register(self, user: User, username: str, passwd: str) -> Any:
        old_username = user.username
        if not self.users[old_username].state.register(username, passwd):
            return None
        with self.lock:
            self.users[username] = self.users[old_username]
            self.users[username].username = username
            del self.users[old_username]
        return self.jwt_encode(username)

    def timeout_handler(self, username: str) -> None:
        with self.lock:
            del self.users[username]
